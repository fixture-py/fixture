

class Loader(object):
    """knows how to setup and teardown a DataSet.
    """
    is_loaded = False
    
    def setup(self, dataset):
        raise NotImplementedError
    
    def teardown(self, dataset):
        raise NotImplementedError

class SOLoader(Loader):
    def __init__(self, dsn=None, connection=None):
        from sqlobject import connectionForURI
        if not connection:
            self.connection = connectionForURI(dsn)
        else:
            self.connection = connection