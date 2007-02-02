
from fixture.loader import DatabaseLoader

class AssignedMapperMedium(DatabaseLoader.StorageMediumAdapter):
    def __init__(self, *a,**kw):
        DatabaseLoader.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        self.session.delete(obj)
        self.session.flush()
    
    def visit_loader(self, loader):
        self.session = loader.session
        
    def save(self, row):
        from sqlalchemy.orm.mapper import Mapper
        obj = self.medium()
        if not isinstance(obj.mapper, Mapper):
            raise ValueError("medium %s must be an instance of %s" % (
                                                            obj, Mapper))
        for attname, val in row.items():
            setattr(obj, attname, val)
        self.session.save(obj)
        self.session.flush()
        return obj
        
class TableMedium(DatabaseLoader.StorageMediumAdapter):
    def __init__(self, *a,**kw):
        DatabaseLoader.StorageMediumAdapter.__init__(self, *a,**kw)
        
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

def is_table(obj):
    from sqlalchemy.schema import Table
    return isinstance(obj, Table)

def negotiated_medium(obj, dataset):
    if is_assigned_mapper(obj):
        return AssignedMapperMedium(obj, dataset)
    elif is_table(obj):
        return TableMedium(obj, dataset)
    else:
        raise NotImplementedError("object %s is not supported by %s" % (
                                                    obj, SqlAlchemyLoader))

class SqlAlchemyLoader(DatabaseLoader):            
    Medium = staticmethod(negotiated_medium)
    
    def __init__(self,  style=None, dsn=None, medium=None, 
                        env=None, session_context=None):
        DatabaseLoader.__init__(self,   style=style, dsn=dsn, 
                                        env=env, medium=medium)
        self.session_context = session_context
        self.session = None
    
    def begin(self, unloading=False):
        
        if self.session_context is None:            
            import sqlalchemy
            from sqlalchemy.ext.sessioncontext import SessionContext
            self.session_context = SessionContext(sqlalchemy.create_session)
        
        self.session = self.session_context.current
        self.connection = self.session.bind_to.connect()
        
        DatabaseLoader.begin(self, unloading=unloading)
    
    def commit(self):
        self.session.flush()
        DatabaseLoader.commit(self)
    
    def create_transaction(self):
        transaction = self.session.create_transaction()
        transaction.add(self.connection)
        return transaction
    
    def rollback(self):
        DatabaseLoader.rollback(self)