
import sys
from fixture.util import ObjRegistry

class Loader(object):
    """knows how to load and unload a DataSet.
    """
    class StorageMediumAdapter(object):
        def __init__(self, medium, dataset):
            self.medium = medium
            self.dataset = dataset
            self.transaction = None
            
        def clear(self, obj):
            raise NotImplementedError
        
        def clearall(self):
            for obj in self.dataset.conf.stored_objects:
                self.clear(obj)
            
        def save(self, row):
            raise NotImplementedError
            
        def share_transaction(self, transaction):
            self.transaction = transaction
            
    Medium = StorageMediumAdapter
            
    class StorageMediaNotFound(LookupError): 
        pass
    
    def __init__(self, style=None, medium=None):
        self.style = style
        if medium:
            self.Medium = medium
        self.data = []
    
    def attach_storage_medium(self):
        pass
    
    def begin(self, unloading=False):
        self.loaded_cache = ObjRegistry()
        if not unloading:
            self.loaded_requirements = {}
            self.data = []
    
    def commit(self):
        raise NotImplementedError
    
    def load(self, data):
        self.begin()
        try:
            for ds in data:
                self.load_dataset(ds)
        except:
            self.rollback()
            raise
        else:
            self.commit()
        
    def load_dataset(self, ds, parent=None):
        if not parent:
            parent = ds
                
        for req_ds in ds.conf.requires:
            req = req_ds()
            self.attach_storage_medium(req)
            
            # hmmm...
            k = self.loaded_cache.id(parent)
            self.loaded_requirements.setdefault(k, [])
            self.loaded_requirements[k].append(req)
            self.load_dataset(req, parent=parent)
        
        # due to reference resolution we might get colliding data sets...
        if ds in self.loaded_cache:
            return
            
        self.attach_storage_medium(ds)
        for key, row in ds:
            ds.conf.storage_medium.share_transaction(self.transaction)
            try:
                obj = ds.conf.storage_medium.save(row)
                ds.conf.stored_objects.append(obj)
            except:
                etype, val, tb = sys.exc_info()
                raise etype, (
                        "%s (while saving '%s' of %s, %s)" % (
                                                val, key, ds, row)), tb
        self.loaded_cache.register(ds)
        self.data.append(ds)
    
    def rollback(self):
        raise NotImplementedError
    
    def unload(self):
        if not self.data:
            return
        
        self.begin(unloading=True)
        try:
            for dataset in self.data:
                self.unload_dataset(dataset)
        except:
            self.rollback()
            raise
        else:
            self.commit()
    
    def unload_dataset(self, dataset):
        dataset.conf.storage_medium.clearall()
        k = self.loaded_cache.id(dataset)
        
        if k in self.loaded_requirements:
            for required_d in self.loaded_requirements[k]:
                required_d.conf.storage_medium.clearall()

class DatabaseLoader(Loader):
    def __init__(self, style=None, dsn=None, env=None, medium=None):
        Loader.__init__(self, style=style, medium=medium)
        self.dsn = dsn
        self.env = env
        self.transaction = None
    
    def attach_storage_medium(self, ds):
            
        if not ds.conf.storage:
            ds.conf.storage = self.style.guess_storage(ds.__class__.__name__)
        if not ds.conf.storage_medium:
            if hasattr(self.env, 'get'):
                ds.conf.storage_medium = self.Medium(self.env.get(
                                                ds.conf.storage, None), ds)
            if not ds.conf.storage_medium:
                if hasattr(self.env, ds.conf.storage):
                    ds.conf.storage_medium = self.Medium(getattr(
                                                self.env, ds.conf.storage), ds)
            
        if not ds.conf.storage_medium:
            repr_env = repr(type(self.env))
            if hasattr(self.env, '__module__'):
                repr_env = "%s from '%s'" % (repr_env, repr_env.__module__)
                
            raise self.StorageMediaNotFound(
                "could not find %s '%s' for "
                "dataset '%s' in self.env (%s)" % (
                    self.Medium, ds.conf.storage, name, repr_env))
    
    def begin(self, unloading=False):
        Loader.begin(self, unloading=unloading)
        self.transaction = self.start_transaction()
    
    def commit(self):
        self.transaction.commit()
    
    def rollback(self):
        self.transaction.rollback()
        