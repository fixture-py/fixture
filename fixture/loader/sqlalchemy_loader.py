
from fixture.loader import DatabaseLoader
session_context = None

class SqlAlchemyLoader(DatabaseLoader):
    
    class AssignedMapperMedium(DatabaseLoader.StorageMediumAdapter):
        def __init__(self, *a,**kw):
            DatabaseLoader.StorageMediumAdapter.__init__(self, *a,**kw)
            self.session = session_context.current
            
        def clear(self, obj):
            obj.delete()
            
        def save(self, row):
            obj = self.medium()
            for attname, val in row.items():
                setattr(obj, attname, val)
            
            obj.save()
            return obj
            
    Medium = AssignedMapperMedium
    
    def __init__(self,  style=None, dsn=None, medium=None, 
                        meta=None, env=None):
        global session_context
        DatabaseLoader.__init__(self,   style=style, dsn=dsn, 
                                        env=env, medium=medium)
        self.meta = meta
        
        if not session_context:
            import sqlalchemy
            from sqlalchemy.ext.sessioncontext import SessionContext
            session_context = SessionContext(
                    lambda: sqlalchemy.create_session(bind_to=self.meta.engine))
            
        self.session = session_context.current
    
    def begin(self, unloading=False):
        DatabaseLoader.begin(self, unloading=unloading)
        if not unloading:
            self.session.clear()
    
    def commit(self):
        self.session.flush()
        DatabaseLoader.commit(self)
    
    def start_transaction(self):
        self.connection = self.meta.engine.contextual_connect()
        transaction = self.connection.begin()
        return transaction
    
    def rollback(self):
        self.session.clear()
        DatabaseLoader.rollback(self)