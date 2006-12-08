

class Loader(object):
    """knows how to setup and teardown a DataSet.
    """
    is_loaded = False
    
    def setup(self, dataset):
        raise NotImplementedError
    
    def teardown(self, dataset):
        raise NotImplementedError

class SOLoader(Loader):
    is_loaded = False