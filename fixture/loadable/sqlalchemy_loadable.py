
"""sqlalchemy fixture components."""

from fixture.loadable import DBLoadableFixture

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
    
    - session_context
    
      - An instance of sqlalchemy.ext.sessioncontext.SessionContext.  A session 
        will be created from session_context.current
    
    - session
      
      - A session from sqlalchemy.create_session().  This will override the 
        session_context.current approach.
    
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
    
    def __init__(self,  style=None, medium=None, env=None, session=None, 
                        session_context=None, dataclass=None):
        DBLoadableFixture.__init__(self,   style=style, dsn=None, 
                                    env=env, medium=medium, dataclass=dataclass)
        self.session = session
        self.session_context = session_context
    
    def begin(self, unloading=False):
        
        if self.session is None:
            ## seems that the problem with supporting dsn and meta is because 
            ## objects can be attached to sessions already
            # if self.session_context is None:            
            #     import sqlalchemy
            #     from sqlalchemy.ext.sessioncontext import SessionContext
            # 
            #     self.session_context = SessionContext(
            #       lambda: sqlalchemy.create_session(bind_to=self.meta.engine))
            self.session = self.session_context.current
        
        if self.session.bind_to is None:
            raise NotImplementedError(
                    "use of a session not bound to an engine is not "
                    "implemented.  needs work in transaction land to make that "
                    "happen, I think.  otherwise, you can use "
                    "create_session(bind_to=engine) instead")
        else:
            self.connection = self.session.bind_to.connect()
        
        DBLoadableFixture.begin(self, unloading=unloading)
    
    def commit(self):
        self.session.flush()
        DBLoadableFixture.commit(self)
    
    def create_transaction(self):
        transaction = self.session.create_transaction()
        transaction.add(self.connection)
        return transaction
    
    def rollback(self):
        DBLoadableFixture.rollback(self)

class MappedClassMedium(DBLoadableFixture.StorageMediumAdapter):
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        self.session.delete(obj)
        self.session.flush()
    
    def visit_loader(self, loader):
        self.session = loader.session
        
    def save(self, row):
        obj = self.medium()
        for attname, val in row.items():
            setattr(obj, attname, val)
        self.session.save(obj)
        self.session.flush()
        return obj
        
class TableMedium(DBLoadableFixture.StorageMediumAdapter):
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        table, primary_key = obj
        i=0
        for k in table.primary_key:
            id = getattr(table.c, k.key)
            stmt = table.delete(id==primary_key[i])
            c = self.connection.execute(stmt)
            i+=1
    
    def visit_loader(self, loader):
        self.connection = loader.connection
        
    def save(self, row):
        from sqlalchemy.schema import Table
        if not isinstance(self.medium, Table):
            raise ValueError(
                "medium %s must be a Table instance" % self.medium)
                
        stmt = self.medium.insert()
        c = self.connection.execute(stmt, 
                                    dict([(k,v) for k,v in row.iteritems()]))
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
        
        return (self.medium, primary_key)

def is_assigned_mapper(obj):
    from sqlalchemy.orm.mapper import Mapper
    return hasattr(obj, 'mapper') and isinstance(obj.mapper, Mapper)

def is_mapped_class(obj):
    from sqlalchemy import util
    return hasattr(obj, 'c') and isinstance(obj.c, util.OrderedProperties)
    
    ## what about this??
    # from sqlalchemy.orm.mapper import Mapper
    # return hasattr(obj, '_mapper') and isinstance(obj._mapper, Mapper)

def is_table(obj):
    from sqlalchemy.schema import Table
    return isinstance(obj, Table)