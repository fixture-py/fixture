
"""sqlobject fixture components."""

from fixture.loadable import DBLoadableFixture

class SQLObjectFixture(DBLoadableFixture):
    """A fixture that knows how to load DataSet objects into sqlobject(s).
    
    Keyword Arguments
    -----------------
    - style
    
      - A Style object to translate names with
     
    - dsn
    
      - A dsn to create a connection with.
    
    - dataclass
    
      - SuperSet to represent loaded data with
    
    - env
    
      - A dict or module that contains SQLObject classes.  The Style object will 
        look here when translating DataSet names into SQLObject class names.
    
    - medium
    
      - A custom StorageMediumAdapter to instantiate when storing a DataSet.
    
    - use_transaction
    
      - If this is true, no data will be loaded or torn down inside a 
        transaction, so it is possible that an IntegrityError will leave 
        partially loaded data behind.
    
    - close_conn
    
      - True if the connection can be closed, helpful for releasing connections.  
        If you are passing in a connection object this will be False by default.
    
    """
            
    def __init__(self,  style=None, dsn=None, medium=None, dataclass=None,
                        connection=None, env=None, use_transaction=True,
                        close_conn=False ):
        DBLoadableFixture.__init__(self, style=style, dsn=dsn, env=env, 
                                            medium=medium, dataclass=dataclass)
        self.connection = connection
        self.close_conn = close_conn
        self.use_transaction = use_transaction
    
    class SQLObjectMedium(DBLoadableFixture.StorageMediumAdapter):
        def clear(self, obj):
            obj.destroySelf()
            
        def save(self, row):
            from sqlobject.styles import getStyle
            so_style = getStyle(self.medium)
    
            if hasattr(row, 'connection'):
                raise ValueError(
                        "cannot name a key 'connection' in row %s" % row)
            dbvals = dict([(so_style.dbColumnToPythonAttr(k), getattr(row, k)) 
                                                        for k in row.columns()])
            dbvals['connection'] = self.transaction
            return self.medium(**dbvals)
        
        def visit_loader(self, loader):
            self.transaction = loader.transaction
            
    Medium = SQLObjectMedium
    
    def create_transaction(self):
        from sqlobject import connectionForURI
        if not self.connection:
            self.connection = connectionForURI(self.dsn)
            self.close_conn = True # because we made it
        if self.use_transaction:
            return self.connection.transaction()
        else:
            return self.connection
    
    def commit(self):
        if self.use_transaction:
            DBLoadableFixture.commit(self)
    
    def then_finally(self, unloading=False):
        if unloading and self.close_conn:
            self.connection.close()
            self.connection = None # necessary for gc
    
    def rollback(self):
        if self.use_transaction:
            DBLoadableFixture.rollback(self)
        