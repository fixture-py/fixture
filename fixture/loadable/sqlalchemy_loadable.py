
"""sqlalchemy fixture components."""

from fixture.loadable import DBLoadableFixture
from fixture.exc import UninitializedError

try:
    from sqlalchemy.orm import sessionmaker, scoped_session
except ImportError:
    Session = None
else:
    Session = scoped_session(sessionmaker(autoflush=False, transactional=True), scopefunc=lambda:__name__)

def negotiated_medium(obj, dataset):
    if is_table(obj):
        return TableMedium(obj, dataset)
    elif is_assigned_mapper(obj):
        return MappedClassMedium(obj, dataset)
    elif is_mapped_class(obj):
        return MappedClassMedium(obj, dataset)
    else:
        raise NotImplementedError("object %s is not supported by %s" % (
                                                    obj, SQLAlchemyFixture))

class SQLAlchemyFixture(DBLoadableFixture):
    """A fixture that knows how to load DataSet objects into sqlalchemy objects.
    
    Keyword Arguments
    -----------------
    - style
    
      - A Style object to translate names with
    
    - scoped_session
    
      - An instance of sqlalchemy.orm.scoped_session.ScopedSession

    - session_context

      - An instance of sqlalchemy.ext.sessioncontext.SessionContext.  A session 
        will be created from session_context.current
    
    - session
      
      - A session from sqlalchemy.create_session().  This will override the 
        ScopedSession and SessionContext approaches.
    
    - connection
    
      - A specific connectable/engine object (must be connected).  This is only 
        necessary if you are working with an unbound session *and* you want to 
        use the TableMedium for data storage.
    
    - dataclass
    
      - SuperSet to represent loaded data with
    
    - env
    
      - A dict or module that contains either mapped classes or Table objects,
        or both.  This will be search when style translates DataSet names into
        storage media.
    
    - medium
    
      - A custom StorageMediumAdapter to instantiate when storing a DataSet.
        By default, a medium adapter will be negotiated based on the type of 
        sqlalchemy object so you should only set this if you know what you 
        doing.
    
    """
    Medium = staticmethod(negotiated_medium)
    
    def __init__(self, engine=None, connection=None, session=None, session_context=None, **kw):
        DBLoadableFixture.__init__(self, **kw)
        self.engine = engine
        self.connection = connection
        self.session = session
        self.session_context = session_context
    
    def begin(self, unloading=False):
        if self.session_context is not None:
            self.session = self.session_context.current
        if self.connection is None and self.engine is None:
            if hasattr(self.session, 'bind'):
                self.engine = self.session.bind
            elif hasattr(self.session, 'bind_to'):
                self.engine = self.session.bind_to
            else:
                raise UninitializedError(
                    "connection= and engine= keywords were not specified; couldn't find "
                    "a connection as session.bind, session.bind_to")
        if self.connection is None:
            self.connection = self.engine.connect()
        
        if self.session is None:
            Session.configure(bind=self.connection)
            self.session = Session()
            
        DBLoadableFixture.begin(self, unloading=unloading)
    
    def commit(self):
        self.session.flush()
        DBLoadableFixture.commit(self)
    
    def create_transaction(self):
        transaction = self.connection.begin()
        # transaction = self.session.create_transaction()
        return transaction
    
    def dispose(self):
        from fixture.dataset import dataset_registry
        dataset_registry.clear()
        if self.connection:
            self.connection.close()
        if self.session:
            if self.session_bind:
                self.session_bind.dispose()
            self.session.close()
        if self.transaction:
            self.transaction.close()
    
    def rollback(self):
        DBLoadableFixture.rollback(self)

## this was used in an if branch of clear() ... but I think this is no longer necessary with scoped sessions
## does it need to exist for 0.3 ?  not sure
# def object_was_deleted(session, obj):
#     # hopefully there is a more future proof way to do this...
#     from sqlalchemy.orm.mapper import object_mapper
#     for c in [obj] + list(object_mapper(obj).cascade_iterator(
#                                                     'delete', obj)):
#         if c in session.deleted:
#             return True
#         elif not session.uow._is_valid(c):
#             # it must have been deleted elsewhere.  is there any other 
#             # reason for this scenario?
#             return True
#     return False

class MappedClassMedium(DBLoadableFixture.StorageMediumAdapter):
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        self.session.delete(obj)
    
    def visit_loader(self, loader):
        self.session = loader.session
        
    def save(self, row, column_vals):
        obj = self.medium()
        for c, val in column_vals:
            setattr(obj, c, val)
        self.session.save(obj)
        return obj
        
class TableMedium(DBLoadableFixture.StorageMediumAdapter):
    class LoadedTableRow(object):
        def __init__(self, table, inserted_key, connection):
            self.table = table
            self.inserted_key = [k for k in inserted_key]
            self.connection = connection
            self.row = None
        
        def __getattr__(self, col):
            if not self.row:
                if len(self.inserted_key) > 1:
                    raise NotImplementedError(
                        "%s does not support making a select statement with a "
                        "composite key, %s.  probably fixable" % (
                                            self.__class__.__name__, 
                                            self.table.primary_key))
                
                first_pk = [k for k in self.table.primary_key][0]
                id = getattr(self.table.c, first_pk.key)
                c = self.connection.execute(self.table.select(
                                                id==self.inserted_key[0]))
                self.row = c.fetchone()
            return getattr(self.row, col)
            
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        i=0
        for k in obj.table.primary_key:
            id = getattr(obj.table.c, k.key)
            stmt = obj.table.delete(id==obj.inserted_key[i])
            c = self.connection.execute(stmt)
            i+=1
    
    def visit_loader(self, loader):
        if loader.connection is None:
            raise UninitializedError(
                "The loader using %s() has a None type connection.  "
                "To fix this, either pass in the connection keyword or use "
                "a session bound to an engine" % (
                    self.__class__.__name__))
        self.connection = loader.connection
        
    def save(self, row, column_vals):
        from sqlalchemy.schema import Table
        if not isinstance(self.medium, Table):
            raise ValueError(
                "medium %s must be a Table instance" % self.medium)
                
        stmt = self.medium.insert()
        c = self.connection.execute(stmt, dict(list(column_vals)))
        primary_key = c.last_inserted_ids()
        if primary_key is None:
            raise NotImplementedError(
                    "what can we do with a None primary key?")
        table_keys = [k for k in self.medium.primary_key]
        inserted_keys = [k for k in primary_key]
        if len(inserted_keys) != len(table_keys):
            raise ValueError(
                "expected primary_key %s, got %s (using table %s)" % (
                                table_keys, inserted_keys, self.medium))
        
        return self.LoadedTableRow(self.medium, primary_key, self.connection)

def is_assigned_mapper(obj):
    from sqlalchemy.orm.mapper import Mapper
    if hasattr(obj, 'is_assigned'):
        # 0.4 :
        is_assigned = obj.is_assigned
    else:
        def is_assigned(obj):
            # 0.3 :
           return hasattr(obj, 'mapper') and isinstance(obj.mapper, Mapper)
    return is_assigned(obj)

def is_mapped_class(obj):
    from sqlalchemy import util
    return hasattr(obj, 'c') and isinstance(obj.c, util.OrderedProperties)

def is_table(obj):
    from sqlalchemy.schema import Table
    return isinstance(obj, Table)
