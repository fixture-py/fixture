
from fixture.loader import DatabaseLoader

class SQLObjectLoader(DatabaseLoader):
    
    class SQLObjectMedium(DatabaseLoader.StorageMediumAdapter):
        def clear(self, obj):
            obj.destroySelf()
            
        def save(self, row):
            from sqlobject.styles import getStyle
            so_style = getStyle(self.medium)
    
            if 'connection' in row:
                raise ValueError(
                        "cannot name a key 'connection' in row %s" % row)
            dbvals = dict([(so_style.dbColumnToPythonAttr(k), v) 
                                                    for k,v in row.items()])
            dbvals['connection'] = self.transaction
            return self.medium(**dbvals)
        
        def visit_loader(self, loader):
            self.transaction = loader.transaction
            
    Medium = SQLObjectMedium
            
    def __init__(self,  style=None, dsn=None, medium=None, 
                        connection=None, env=None, use_transaction=True):
        DatabaseLoader.__init__(self, style=style, dsn=dsn, env=env, 
                                                    medium=medium)
        self.connection = connection
        self.use_transaction = use_transaction
    
    def create_transaction(self):
        from sqlobject import connectionForURI
        if not self.connection:
            self.connection = connectionForURI(self.dsn)
        if self.use_transaction:
            return self.connection.transaction()
        else:
            return self.connection
    
    def commit(self):
        if self.use_transaction:
            DatabaseLoader.commit(self)
    
    def rollback(self):
        if self.use_transaction:
            DatabaseLoader.rollback(self)
        