
import sys

class Loader(object):
    """knows how to load and unload a DataSet.
    """
    class StorageMediaNotFound(LookupError): 
        pass

class SOLoader(Loader):
    def __init__(self,  dsn=None, connection=None, 
                        env=None, style=None):
        from sqlobject import connectionForURI
        if not connection:
            self.connection = connectionForURI(dsn)
        else:
            self.connection = connection
        
        self.env = env
        self.style = style
        self.transaction = None
    
    def __repr__(self):
        return "<SQLObject Loader at %s>" % (hex(id(self)))
    
    def begin(self):
        self.transaction = self.connection.transaction()
    
    def commit(self):
        self.transaction.commit()
    
    def load(self, data):
        for dataset in data:
            # print key, dataset
            dataset_name = dataset.__class__.__name__
            if not dataset._storage:
                dataset._storage = self.style.guess_storage(dataset_name)
            if not dataset._storage_medium:
                if hasattr(self.env, 'get'):
                    dataset._storage_medium = self.env.get(
                                                    dataset._storage, None)
                if not dataset._storage_medium:
                    if hasattr(self.env, dataset._storage):
                        dataset._storage_medium = getattr(
                                                    self.env, dataset._storage)
                
            if not dataset._storage_medium:
                repr_env = repr(type(self.env))
                if hasattr(self.env, '__module__'):
                    repr_env = "%s from '%s'" % (repr_env, repr_env.__module__)
                    
                raise self.StorageMediaNotFound(
                    "could not find SQLObject '%s' for "
                    "dataset '%s' in self.env (%s)" % (
                        dataset._storage, dataset_name, repr_env))
            
            self.load_dataset(dataset)
    
    def load_dataset(self, dataset):
        from sqlobject.styles import getStyle
        
        so_style = getStyle(dataset._storage_medium)
        for key, row in dataset:
            # make this abstract for mixing media ?
            dbvals = dict([(so_style.dbColumnToPythonAttr(k), v) 
                                                    for k,v in row.items()])
            dbvals['connection'] = self.transaction
            try:
                dataset._storage_medium(**dbvals)
            except:
                etype, val, tb = sys.exc_info()
                raise etype, (
                        "%s (while loading key '%s' of %s, db values %s)" % (
                                                val, key, dataset, dbvals)), tb
    
    def unload(self, data):
        datasets = [d for d in data]
        datasets.reverse()
        for dataset in datasets:
            dataset._storage_medium.clearTable()
            