
import sys
from fixture.base import Fixture
from fixture.util import ObjRegistry, _mklog
from fixture.style import NamedDataStyle
from fixture.dataset import Ref, dataset_registry, DataRow
from fixture.exc import LoadError, UnloadError
import logging

log = _mklog("fixture.loadable")
treelog = _mklog("fixture.loadable.tree")

class LoadableFixture(Fixture):
    """A fixture that knows how to load and unload a DataSet.
    
    This ia an abstract class and cannot be used directly.  You can use a 
    LoadableFixture that already knows how to load into a specific medium, such 
    as SQLAlchemyFixture
    
    Keyword Arguments
    -----------------
    - dataclass
        
      - class to instantiate with datasets (defaults to that of Fixture)
    
    - style
    
      - a Style object to translate names with (defaults to NamedDataStyle)
     
    - medium
    
      - optional LoadableFixture.StorageMediumAdapter to store DataSet 
        objects with
    
    """
    style = NamedDataStyle()
    dataclass = Fixture.dataclass
    
    def __init__(self, style=None, medium=None, dataclass=None):
        Fixture.__init__(self, loader=self, dataclass=dataclass)
        if style:
            self.style = style
        if medium:
            self.Medium = medium
    
    class StorageMediumAdapter(object):
        def __init__(self, medium, dataset):
            self.medium = medium
            self.dataset = dataset
            self.transaction = None
        
        def __getattr__(self, name):
            return getattr(self.obj, name)
        
        def __repr__(self):
            return "%s at %s for %s" % (
                    self.__class__.__name__, hex(id(self)), self.medium)
            
        def clear(self, obj):
            raise NotImplementedError
        
        def clearall(self):
            log.info("CLEARING stored objects for %s", self.dataset)
            for obj in self.dataset.meta._stored_objects:
                try:
                    self.clear(obj)
                except Exception, e:
                    etype, val, tb = sys.exc_info()
                    raise UnloadError(etype, val, self.dataset, 
                                         stored_object=obj), None, tb
            
        def save(self, row):
            raise NotImplementedError
            
        def visit_loader(self, loader):
            pass
            
    Medium = StorageMediumAdapter
            
    class StorageMediaNotFound(LookupError): 
        pass
    
    class LoadQueue(ObjRegistry):
        """Keeps track of what class instances were loaded
        
        """
        # >>> class Foo: 
        # ...     name = 'foo'
        # ...
        # >>> class Bar: 
        # ...     name = 'bar'
        # ...
        # >>> q = LoadableFixture.LoadQueue()
        # >>> assert q.register(Foo()) is not None
        # >>> Foo() in q
        # True
        # >>> assert q.register(Bar()) is not None
        # >>> [ o.name for o in q.to_unload() ]
        # ['bar', 'foo']
        # >>> q.referenced(Foo())
        # >>> [ o.name for o in q.to_unload() ]
        # ['foo', 'bar']

        def __init__(self):
            ObjRegistry.__init__(self)
            self.levels = {}
        
        def __repr__(self):
            return "<%s at %s %s>" % (
                    self.__class__.__name__, hex(id(self)), 
                    [self.registry[i].__class__ for i in self.unload_queue])
        
        def register(self, obj, level):
            """register this object as "loaded"  
            """
            id = ObjRegistry.register(self, obj)
            self.levels.setdefault(level, [])
            self.levels[level].insert(0, id)
            return id
        
        def referenced(self, obj, level):
            """tell the queue that this object is referenced again.
            """
            id = self.id(obj)
            self.levels.setdefault(level, [])
            self.levels[level].append(id)
            # if id in self.levels[level]:
            #     self.levels[level].remove(id)
            # self.levels[level].insert(0, id)
        
        def to_unload(self):
            """yields a list of objects suitable for unloading.
            
            in order of last object touched first, so that we can build a stack 
            of row objects and their dependent objects (foreign keys), allowing 
            foreign keys to be referenced more than once.
            """
            level_nums = self.levels.keys()
            level_nums.sort()
            unloaded = set() # only unload once
            for level in level_nums:
                unload_queue = [id for id in self.levels[level] 
                                                if id not in unloaded]
                # print level, [self.registry[i].__class__.__name__ 
                #                                 for i in unload_queue]
                for id in unload_queue: 
                    yield self.registry[id]
                    unloaded.add(id)
    
    def attach_storage_medium(self):
        pass
    
    def begin(self, unloading=False):
        if not unloading:
            self.loaded = self.LoadQueue()
    
    def commit(self):
        raise NotImplementedError
    
    def load(self, data):
        def loader():
            for ds in data:
                self.load_dataset(ds)
        self.wrap_in_transaction(loader, unloading=False)
        
    def load_dataset(self, ds, level=0):
        
        levsep = level==0 and "/--------" or "|__.."
        treelog.info(
            "%s%s%s (%s)", level * '  ', levsep, ds.__class__.__name__, level)
        
        for ref_ds in ds.meta.references:
            r = ref_ds.shared_instance(default_refclass=self.dataclass)
            self.load_dataset(r, level=level+1)
        
        self.attach_storage_medium(ds)
        
        if ds in self.loaded:
            self.loaded.referenced(ds, level)
            return
        
        log.info("LOADING rows in %s", ds)
        ds.meta.storage_medium.visit_loader(self)
        for key, row in ds:
            try:
                # resolve this row's referenced values :
                for k in row.columns():
                    v = getattr(row, k)
                    if isinstance(v, Ref.Value):
                        ref = v.ref
                        ref.dataset_obj = self.loaded[ref.dataset_class]
                        isref=True
                
                if not isinstance(row, DataRow):
                    row = row(ds)
                obj = ds.meta.storage_medium.save(row)
                ds.meta._stored_objects.store(key, obj)
                # save the instance in place of the class...
                ds._setdata(key, row)
                
            except Exception, e:
                etype, val, tb = sys.exc_info()
                raise self.LoadError(etype, val, ds, key=key, row=row), None, tb
        
        self.loaded.register(ds, level)
    
    def rollback(self):
        raise NotImplementedError
    
    def then_finally(self, unloading=False):
        pass
    
    def unload(self):
        def unloader():
            for dataset in self.loaded.to_unload():
                self.unload_dataset(dataset)
            dataset_registry.clear()
        self.wrap_in_transaction(unloader, unloading=True)
    
    def unload_dataset(self, dataset):
        dataset.meta.storage_medium.clearall()
    
    def wrap_in_transaction(self, routine, unloading=False):
        self.begin(unloading=unloading)
        try:
            try:
                routine()
            except:
                self.rollback()
                raise
            else:
                self.commit()
        finally:
            self.then_finally(unloading=unloading)

class EnvLoadableFixture(LoadableFixture):
    """An abstract fixture that can resolve DataSet objects from an env.
    
    Keyword "env" should be a dict or a module if not None.
    According to the style rules, the env will be used to find objects by name.
    
    """
    def __init__(self, env=None, **kw):
        LoadableFixture.__init__(self, **kw)
        self.env = env
    
    def attach_storage_medium(self, ds):
        
        if ds.meta.storage_medium is not None:
            # already attached...
            return
        
        storable = ds.meta.storable
        
        if not storable:
            if not ds.meta.storable_name:
                ds.meta.storable_name = self.style.guess_storable_name(
                                                        ds.__class__.__name__)
        
            if hasattr(self.env, 'get'):
                storable = self.env.get(ds.meta.storable_name, None)
            if not storable:
                if hasattr(self.env, ds.meta.storable_name):
                    try:
                        storable = getattr(self.env, ds.meta.storable_name)
                    except AttributeError:
                        pass
        
            if not storable:
                repr_env = repr(type(self.env))
                if hasattr(self.env, '__module__'):
                    repr_env = "%s from '%s'" % (repr_env, self.env.__module__)
                
                raise self.StorageMediaNotFound(
                    "could not find %s '%s' for "
                    "dataset %s in self.env (%s)" % (
                        self.Medium, ds.meta.storable_name, ds, repr_env))
                        
        ds.meta.storage_medium = self.Medium(storable, ds)

class DBLoadableFixture(EnvLoadableFixture):
    """An abstract fixture that will be loadable into a database.
    
    More specifically, one that forces its implementation to run atomically 
    (within a begin/ commit/ rollback block).
    """
    def __init__(self, dsn=None, **kw):
        EnvLoadableFixture.__init__(self, **kw)
        self.dsn = dsn
        self.transaction = None
    
    def begin(self, unloading=False):
        EnvLoadableFixture.begin(self, unloading=unloading)
        self.transaction = self.create_transaction()
    
    def commit(self):
        self.transaction.commit()
    
    def create_transaction(self):
        raise NotImplementedError
    
    def rollback(self):
        self.transaction.rollback()
        