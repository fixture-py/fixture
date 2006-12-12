
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
        for ds in data:
            ds_name = ds.__class__.__name__
            if not ds.conf.storage:
                ds.conf.storage = self.style.guess_storage(ds_name)
            if not ds.conf.storage_medium:
                if hasattr(self.env, 'get'):
                    ds.conf.storage_medium = self.env.get(
                                                    ds.conf.storage, None)
                if not ds.conf.storage_medium:
                    if hasattr(self.env, ds.conf.storage):
                        ds.conf.storage_medium = getattr(
                                                self.env, ds.conf.storage)
                
            if not ds.conf.storage_medium:
                repr_env = repr(type(self.env))
                if hasattr(self.env, '__module__'):
                    repr_env = "%s from '%s'" % (repr_env, repr_env.__module__)
                    
                raise self.StorageMediaNotFound(
                    "could not find SQLObject '%s' for "
                    "dataset '%s' in self.env (%s)" % (
                        ds.conf.storage, ds_name, repr_env))
            
            self.load_dataset(ds)
    
    def load_dataset(self, dataset):
        from sqlobject.styles import getStyle
        
        so_style = getStyle(dataset.conf.storage_medium)
        for key, row in dataset:
            # make this abstract for mixing media ?
            dbvals = dict([(so_style.dbColumnToPythonAttr(k), v) 
                                                    for k,v in row.items()])
            dbvals['connection'] = self.transaction
            try:
                dataset.conf.storage_medium(**dbvals)
            except:
                etype, val, tb = sys.exc_info()
                raise etype, (
                        "%s (while loading key '%s' of %s, db values %s)" % (
                                                val, key, dataset, dbvals)), tb
    
    def unload(self, data):
        datasets = [d for d in data]
        datasets.reverse()
        for dataset in datasets:
            dataset.conf.storage_medium.clearTable()
            