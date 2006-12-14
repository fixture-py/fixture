
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
        self.data = []
    
    def __repr__(self):
        return "<SQLObject Loader at %s>" % (hex(id(self)))
    
    def begin(self, unloading=False):
        self.transaction = self.connection.transaction()
        self.loaded_cache = {}
        if not unloading:
            self.loaded_requirements = {}
            self.data = []
    
    def commit(self):
        self.transaction.commit()
    
    def get_dataset_name(self, dataset):
        # should this be the style's responsibility?
        return dataset.__class__.__name__
    
    def init_dataset(self, ds, name=None):
        if not name:
            name = self.get_dataset_name(ds)
            
        if not ds.conf.storage:
            ds.conf.storage = self.style.guess_storage(name)
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
                    ds.conf.storage, name, repr_env))
    
    def load(self, data):
        self.begin()     
        for ds in data:
            self.load_dataset(ds)
        self.commit()
    
    def load_dataset(self, ds, parent=None):
        if not parent:
            parent = ds
                
        for req_ds in ds.conf.requires:
            req = req_ds()
            self.init_dataset(req)
            
            k = self.get_dataset_name(parent)
            self.loaded_requirements.setdefault(k, [])
            self.loaded_requirements[k].append(req)
            self.load_dataset(req, parent=parent)
        
        
        # due to reference resolution we might get colliding data sets...
        cache_id = id(ds.__class__)
        
        if cache_id in self.loaded_cache:
            return
            
        self.init_dataset(ds)
        from sqlobject.styles import getStyle
        so_style = getStyle(ds.conf.storage_medium)
        for key, row in ds:
            # make this abstract for mixing media ?
            dbvals = dict([(so_style.dbColumnToPythonAttr(k), v) 
                                                    for k,v in row.items()])
            dbvals['connection'] = self.transaction
            try:
                ds.conf.storage_medium(**dbvals)
            except:
                etype, val, tb = sys.exc_info()
                raise etype, (
                        "%s (while loading key '%s' of %s, db values %s)" % (
                                                val, key, ds, dbvals)), tb
        
        self.loaded_cache[cache_id] = 1
        self.data.append(ds)
    
    def unload(self):
        if not self.data:
            return
        def unload_d(d):
            # make this abstract for mixing media?
            d.conf.storage_medium.clearTable()
        
        self.begin(unloading=True)
        for dataset in self.data:
            unload_d(dataset)
            d_name = self.get_dataset_name(dataset)
            if d_name in self.loaded_requirements:
                for required_d in self.loaded_requirements[d_name]:
                    unload_d(required_d)
        
        self.commit()
        