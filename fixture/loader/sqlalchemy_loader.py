
from fixture.loader import DatabaseLoader

class SqlAlchemyLoader(DatabaseLoader):
    
    class AssignedMapperMedium(DatabaseLoader.StorageMediumAdapter):
        def __init__(self, *a,**kw):
            DatabaseLoader.StorageMediumAdapter.__init__(self, *a,**kw)
            
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
            
    Medium = AssignedMapperMedium
    
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
        
        DatabaseLoader.begin(self, unloading=unloading)
    
    def commit(self):
        self.session.flush()
        DatabaseLoader.commit(self)
    
    def start_transaction(self):
        transaction = self.session.create_transaction()
        return transaction
    
    def rollback(self):
        # self.session.clear()
        DatabaseLoader.rollback(self)