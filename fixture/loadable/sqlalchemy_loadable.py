
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
    
    def __init__(self,  session=None, session_context=None, **kw):
        DBLoadableFixture.__init__(self, **kw)
        self.session = session
        self.session_context = session_context
    
    def begin(self, unloading=False):
        
        if self.session is None:
            self.session = self.session_context.current
        
        if self.session.bind_to is None:            
            # note to self:
            # if we don't have a session or session_context, this is the way to 
            # manage engine transactions:
            # http://www.sqlalchemy.org/docs/dbengine.myt#dbengine_transactions
            # (not yet implemented)
            
            # ... OR ... can we not just accept a connection keyword, create an 
            # empty transaction, then add the connection to the transaction?
            # This would cause MappedClassMedium to fail, because it needs a 
            # session
            
            raise NotImplementedError(
                    "Use of an unbound session is not implemented.  It needs "
                    "work in transaction land to make that happen.  "
                    "Otherwise, you can bind your session with "
                    "create_session(bind_to=engine)" )
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
    
    def dispose(self):
        from fixture.dataset import dataset_registry
        dataset_registry.clear()
        if self.connection:
            self.connection.close()
        if self.session.bind_to:
            self.session.bind_to.dispose()
        if self.session:
            self.session.close()
        if self.transaction:
            self.transaction.close()
    
    def rollback(self):
        DBLoadableFixture.rollback(self)

class MappedClassMedium(DBLoadableFixture.StorageMediumAdapter):
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        
        # hopefully there is a more future proof way to do this...
        
        from sqlalchemy.orm.mapper import object_mapper as _object_mapper
        for c in [obj] + list(_object_mapper(obj).cascade_iterator(
                                                        'delete', obj)):
            if c not in self.session.uow.deleted:
                if not self.session.uow._is_valid(c):
                    # it must have been deleted elsewhere.  is there any other 
                    # reason for this scenario?
                    return
                    
        self.session.delete(obj)
        self.session.flush()
    
    def visit_loader(self, loader):
        self.session = loader.session
        
    def save(self, row):
        obj = self.medium()
        for c in row.columns():
            setattr(obj, c, getattr(row, c))
        self.session.save(obj)
        self.session.flush()
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
        self.connection = loader.connection
        
    def save(self, row):
        from sqlalchemy.schema import Table
        if not isinstance(self.medium, Table):
            raise ValueError(
                "medium %s must be a Table instance" % self.medium)
                
        stmt = self.medium.insert()
        c = self.connection.execute(stmt, 
                            dict([(c, getattr(row, c)) for c in row.columns()]))
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
    return hasattr(obj, 'mapper') and isinstance(obj.mapper, Mapper)

def is_mapped_class(obj):
    from sqlalchemy import util
    return hasattr(obj, 'c') and isinstance(obj.c, util.OrderedProperties)

def is_table(obj):
    from sqlalchemy.schema import Table
    return isinstance(obj, Table)