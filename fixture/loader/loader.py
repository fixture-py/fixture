
import sys
from fixture.util import ObjRegistry
from fixture.style import NamedDataStyle

class Loader(object):
    """knows how to load and unload a DataSet.
    """
    class LoadError(Exception):
        pass
        
    style = NamedDataStyle()
    
    class StorageMediumAdapter(object):
        def __init__(self, medium, dataset):
            self.medium = medium
            self.dataset = dataset
            self.transaction = None
        
        def __repr__(self):
            return "%s at %s for %s" % (
                    self.__class__.__name__, hex(id(self)), self.medium)
            
        def clear(self, obj):
            raise NotImplementedError
        
        def clearall(self):
            for obj in self.dataset.meta.stored_objects:
                self.clear(obj)
            
        def save(self, row):
            raise NotImplementedError
            
        def visit_loader(self, loader):
            pass
            
    Medium = StorageMediumAdapter
            
    class StorageMediaNotFound(LookupError): 
        pass
    
    class LoadQueue(ObjRegistry):
        """keeps track of what class instances were loaded
        
        >>> class Foo: 
        ...     name = 'foo'
        ...
        >>> class Bar: 
        ...     name = 'bar'
        ...
        >>> q = Loader.LoadQueue()
        >>> assert q.register(Foo()) is not None
        >>> Foo() in q
        True
        >>> assert q.register(Bar()) is not None
        >>> [ o.name for o in q.to_unload() ]
        ['bar', 'foo']
        >>> q.referenced(Foo())
        >>> [ o.name for o in q.to_unload() ]
        ['foo', 'bar']
        
        """
        def __init__(self):
            ObjRegistry.__init__(self)
            self.queue = []
        
        def register(self, obj):
            """register this object as "loaded"  
            """
            id = ObjRegistry.register(self, obj)
            self.queue.insert(0, id)
            return id
        
        def referenced(self, obj):
            """tell the queue that this object is referenced again.
            """
            id = self.id(obj)
            self.queue.pop(self.queue.index(id))
            self.queue.insert(0, id)
        
        def to_unload(self):
            """yields a list of objects suitable for unloading.
            
            in order of last object touched first, so that we can build a stack 
            of row objects and their dependent objects (foreign keys), allowing 
            foreign keys to be referenced more than once.
            """
            for id in self.queue: 
                yield self.registry[id]
    
    def __init__(self, style=None, medium=None):
        if style:
            self.style = style
        if medium:
            self.Medium = medium
        self.data = []
    
    def attach_storage_medium(self):
        pass
    
    def begin(self, unloading=False):
        if not unloading:
            self.loaded = self.LoadQueue()
    
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
        
    def load_dataset(self, ds):
                
        for req_ds in ds.meta.requires:
            r = req_ds()
            self.load_dataset(r)
        
        self.attach_storage_medium(ds)
        
        if ds in self.loaded:
            self.loaded.referenced(ds)
            return
        
        ds.meta.storage_medium.visit_loader(self)
        for key, row in ds:
            try:
                obj = ds.meta.storage_medium.save(row)
                ds.meta.stored_objects.append(obj)
            except Exception, e:
                etype, val, tb = sys.exc_info()
                raise self.LoadError(
                        "%s: %s (while saving '%s' of %s, %s)" % (
                                etype.__name__, val, key, ds, row)), None, tb
                                                
        self.loaded.register(ds)
    
    def rollback(self):
        raise NotImplementedError
    
    def unload(self):
        self.begin(unloading=True)
        try:
            for dataset in self.loaded.to_unload():
                self.unload_dataset(dataset)
        except:
            self.rollback()
            raise
        else:
            self.commit()
    
    def unload_dataset(self, dataset):
        dataset.meta.storage_medium.clearall()
                

class DatabaseLoader(Loader):
    def __init__(self, style=None, dsn=None, env=None, medium=None):
        Loader.__init__(self, style=style, medium=medium)
        self.dsn = dsn
        self.env = env
        self.transaction = None
    
    def attach_storage_medium(self, ds):
        
        if ds.meta.storage_medium is not None:
            # already attached...
            return
            
        if not ds.meta.storage:
            ds.meta.storage = self.style.guess_storage(ds.__class__.__name__)
        
        storable = None
        
        if hasattr(self.env, 'get'):
            storable = self.env.get(ds.meta.storage, None)
        if not storable:
            if hasattr(self.env, ds.meta.storage):
                try:
                    storable = getattr(self.env, ds.meta.storage)
                except AttributeError:
                    pass
        
        if storable:
            ds.meta.storage_medium = self.Medium(storable, ds)
        else:
            repr_env = repr(type(self.env))
            if hasattr(self.env, '__module__'):
                repr_env = "%s from '%s'" % (repr_env, repr_env.__module__)
                
            raise self.StorageMediaNotFound(
                "could not find %s '%s' for "
                "dataset %s in self.env (%s)" % (
                    self.Medium, ds.meta.storage, ds, repr_env))
    
    def begin(self, unloading=False):
        Loader.begin(self, unloading=unloading)
        self.transaction = self.create_transaction()
    
    def commit(self):
        self.transaction.commit()
    
    def create_transaction(self):
        raise NotImplementedError
    
    def rollback(self):
        self.transaction.rollback()
        