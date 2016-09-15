
"""Abstract classes for :class:`fixture.base.Fixture` descendants that load / unload data

See :ref:`Using LoadableFixture<using-loadable-fixture>` for examples.

"""
# from __future__ import with_statement
__all__ = ['LoadableFixture', 'EnvLoadableFixture', 'DBLoadableFixture', 'DeferredStoredObject']
import sys
import types

from six import reraise

from fixture.base import Fixture
from fixture.dataset import Ref, dataset_registry, DataRow, is_rowlike
from fixture.exc import UninitializedError, LoadError, UnloadError, StorageMediaNotFound
from fixture.style import OriginalStyle
from fixture.util import ObjRegistry, _mklog


log     = _mklog("fixture.loadable")
treelog = _mklog("fixture.loadable.tree")

class StorageMediumAdapter(object):
    """common interface for working with storable objects.
    """
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
        """Must clear the stored object.
        """
        raise NotImplementedError
    
    def clearall(self):
        """Must clear all stored objects.
        """
        log.info("CLEARING stored objects for %s", self.dataset)
        for obj in self.dataset.meta._stored_objects:
            try:
                self.clear(obj)
            except Exception:
                etype, val, tb = sys.exc_info()
                reraise(
                    UnloadError,
                    UnloadError(etype, val, self.dataset, stored_object=obj),
                )
        
    def save(self, row, column_vals):
        """Given a DataRow, must save it somehow.
        
        column_vals is an iterable of (column_name, column_value)
        """
        raise NotImplementedError
        
    def visit_loader(self, loader):
        """A chance to visit the LoadableFixture object.
        
        By default it does nothing.
        """
        pass

class LoadQueue(ObjRegistry):
    """Keeps track of what class instances were loaded.
    
    "level" is used like so:
        
    The lower the level, the lower that object is on the foreign key chain.  
    As the level increases, this means more foreign objects depend on the 
    local object.  Thus, objects need to be unloaded starting at the lowest 
    level and working up.  Also, since objects can appear multiple times in 
    foreign key chains, the queue only acknowledges the object at its 
    highest level, since this will ensure all dependencies get unloaded 
    before it.  
    
    """

    def __init__(self):
        ObjRegistry.__init__(self)
        self.tree = {}
        self.limit = {}
    
    def __repr__(self):
        return "<%s at %s>" % (
                self.__class__.__name__, hex(id(self)))
    
    def _pushid(self, id, level):
        if id in self.limit:
            # only store the object at its highest level:
            if level > self.limit[id]:
                self.tree[self.limit[id]].remove(id)
                del self.limit[id]
            else:
                return
        self.tree.setdefault(level, [])
        self.tree[level].append(id)
        self.limit[id] = level
    
    def clear(self):
        """clear internal registry"""
        ObjRegistry.clear(self)
        # this is an attempt to free up refs to database connections:
        self.tree = {}
        self.limit = {}
    
    def register(self, obj, level):
        """register this object as "loaded" at level
        """
        id = ObjRegistry.register(self, obj)
        self._pushid(id, level)
        return id
    
    def referenced(self, obj, level):
        """tell the queue that this object was referenced again at level.
        """
        id = self.id(obj)
        self._pushid(id, level)
    
    def to_unload(self):
        """yields a list of objects in an order suitable for unloading.
        """
        level_nums = sorted(self.tree.keys())
        treelog.info("*** unload order ***")
        for level in level_nums:
            unload_queue = self.tree[level]
            verbose_obj = []
            
            for id in unload_queue:
                obj = self.registry[id]
                verbose_obj.append(obj.__class__.__name__)
                yield obj
            
            treelog.info("%s. %s", level, verbose_obj)
            
class LoadableFixture(Fixture):
    """
    knows how to load data into something useful.
    
    This is an abstract class and cannot be used directly.  You can use a 
    LoadableFixture that already knows how to load into a specific medium, 
    such as SQLAlchemyFixture, or create your own to build your own to load 
    DataSet objects into custom storage media.

    Keyword Arguments:
    
    dataclass
        class to instantiate with datasets (defaults to that of Fixture)
    style
        a Style object to translate names with (defaults to NamedDataStyle)
    medium
        optional LoadableFixture.StorageMediumAdapter to store DataSet 
        objects with
    
    """
    style = OriginalStyle()
    dataclass = Fixture.dataclass
    
    def __init__(self, style=None, medium=None, **kw):
        Fixture.__init__(self, loader=self, **kw)
        if style:
            self.style = style
        if medium:
            self.Medium = medium
        self.loaded = None
    
    StorageMediumAdapter = StorageMediumAdapter
    Medium = StorageMediumAdapter
    StorageMediaNotFound = StorageMediaNotFound
    LoadQueue = LoadQueue
    
    def attach_storage_medium(self, ds):
        """attach a :class:`StorageMediumAdapter` to DataSet"""
        raise NotImplementedError
    
    def begin(self, unloading=False):
        """begin loading"""
        if not unloading:
            self.loaded = self.LoadQueue()
    
    def commit(self):
        """commit load transaction"""
        raise NotImplementedError
    
    def load(self, data):
        """load data"""
        def loader():
            for ds in data:
                self.load_dataset(ds)
        self.wrap_in_transaction(loader, unloading=False)
        
    def load_dataset(self, ds, level=1):
        """load this dataset and all its dependent datasets.
        
        level is essentially the order of processing (going from dataset to 
        dependent datasets).  Child datasets are always loaded before the 
        parent.  The level is important for visualizing the chain of 
        dependencies : 0 is the bottom, and thus should be the first set of 
        objects unloaded
        
        """
        is_parent = level==1
        
        levsep = is_parent and "/--------" or "|__.."
        treelog.info(
            "%s%s%s (%s)", level * '  ', levsep, ds.__class__.__name__, 
                                            (is_parent and "parent" or level))
        
        for ref_ds in ds.meta.references:
            r = ref_ds.shared_instance(default_refclass=self.dataclass)
            new_level = level+1
            self.load_dataset(r,  level=new_level)
        
        self.attach_storage_medium(ds)
        
        if ds in self.loaded:
            # keep track of its order but don't actually load it...
            self.loaded.referenced(ds, level)
            return
        
        log.info("LOADING rows in %s", ds)
        ds.meta.storage_medium.visit_loader(self)
        registered = False
        for key, row in ds:
            try:
                self.resolve_row_references(ds, row)
                if not isinstance(row, DataRow):
                    row = row(ds)
                def column_vals():
                    for c in row.columns():
                        yield (c, self.resolve_stored_object(getattr(row, c)))
                obj = ds.meta.storage_medium.save(row, column_vals())
                ds.meta._stored_objects.store(key, obj)
                # save the instance in place of the class...
                ds._setdata(key, row)
                if not registered:
                    self.loaded.register(ds, level)
                    registered = True
                
            except Exception:
                etype, val, tb = sys.exc_info()
                reraise(LoadError, LoadError(etype, val, ds, key=key, row=row))
    
    def resolve_row_references(self, current_dataset, row):        
        """resolve this DataRow object's referenced values.
        """
        def resolved_rowlike(rowlike):
            key = rowlike.__name__
            if rowlike._dataset is type(current_dataset):
                return DeferredStoredObject(rowlike._dataset, key)
            loaded_ds = self.loaded[rowlike._dataset]
            return loaded_ds.meta._stored_objects.get_object(key)
        def resolve_stored_object(candidate):            
            if is_rowlike(candidate):
                return resolved_rowlike(candidate)
            else:
                # then it is the stored object itself.  this would happen if 
                # there is a reciprocal foreign key (i.e. organization has a 
                # parent organization)
                return candidate
                
        for name in row.columns():
            val = getattr(row, name)
            if isinstance(val, (list, tuple)):
                # i.e. categories = [python, ruby]
                setattr(row, name, list(map(resolve_stored_object, val)))
            elif isinstance(val, set):
                # i.e. categories = {python, ruby}
                setattr(row, name, set(resolve_stored_object(v) for v in val))
            elif is_rowlike(val):
                # i.e. category = python
                setattr(row, name, resolved_rowlike(val))
            elif isinstance(val, Ref.Value):
                # i.e. category_id = python.id.
                ref = val.ref
                # now the ref will return the attribute from a stored object 
                # when __get__ is invoked
                ref.dataset_obj = self.loaded[ref.dataset_class]
    
    def rollback(self):
        """rollback load transaction"""
        raise NotImplementedError
    
    def then_finally(self, unloading=False):
        """called in a finally block after load transaction has begun"""
        pass
    
    def unload(self):
        """unload data"""
        if self.loaded is None:
            raise UninitializedError(
                "Cannot unload data because it has not yet been loaded in this "
                "process.  Call data.setup() before data.teardown()")
        def unloader():
            for dataset in self.loaded.to_unload():
                self.unload_dataset(dataset)
            self.loaded.clear()
            dataset_registry.clear()
        self.wrap_in_transaction(unloader, unloading=True)
    
    def unload_dataset(self, dataset):
        """unload data stored for this dataset"""
        dataset.meta.storage_medium.clearall()
    
    def wrap_in_transaction(self, routine, unloading=False):
        """call routine in a load transaction"""
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
        """Lookup a storage medium in the ``env`` and attach it to a DataSet.
        
        A storage medium is looked up by name.  If a specific name has not been declared in the DataSet 
        then it will be guessed using the :meth:`Style.guess_storable_name <fixture.style.Style.guess_storable_name>` method.  
        
        Once a name is found (typically the name of a DataSet class, say, EmployeeData) then it is looked up 
        in the ``env`` which is expected to be a dict or module like object.
        
        The method first tries ``env.get('EmployeeData')`` then ``getattr(env, 'EmployeeData')``.
        
        The return value is the storage medium (i.e. a data mapper for the Employees table)
        
        Note that a :mod:`style <fixture.style>` might translate a name to maintain a consistent 
        naming scheme between DataSet classes and data mappers.
        
        """
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
                        
        if storable == ds.__class__:
            raise ValueError(
                "cannot use %s %s as a storable object of itself! "
                "(perhaps your style object was not configured right?)" % (
                                        ds.__class__.__name__, ds.__class__))
        ds.meta.storage_medium = self.Medium(storable, ds)
        
    def resolve_stored_object(self, column_val):
        if type(column_val)==DeferredStoredObject:
            return column_val.get_stored_object_from_loader(self)
        else:
            return column_val

class DBLoadableFixture(EnvLoadableFixture):
    """
    An abstract fixture that can load a DataSet into a database like thing.
    
    More specifically, one that forces its implementation to run atomically 
    (within a begin / commit / rollback block).
    """
    def __init__(self, dsn=None, **kw):
        EnvLoadableFixture.__init__(self, **kw)
        self.dsn = dsn
        self.transaction = None
    
    def begin(self, unloading=False):
        """begin loading data"""
        EnvLoadableFixture.begin(self, unloading=unloading)
        self.transaction = self.create_transaction()
    
    def commit(self):
        """call transaction.commit() on transaction returned by :meth:`DBLoadableFixture.create_transaction`"""
        self.transaction.commit()
    
    def create_transaction(self):
        """must return a transaction object that implements commit() and rollback()
        
        .. note:: transaction.begin() will not be called.  If that is necessary then call begin before returning the object.
        
        """
        raise NotImplementedError
    
    def rollback(self):
        """call transaction.rollback() on transaction returned by :meth:`DBLoadableFixture.create_transaction`"""
        self.transaction.rollback()

class DeferredStoredObject(object):
    """A stored representation of a row in a DataSet, deferred.
    
    The actual stored object can only be resolved by the StoredMediumAdapter 
    itself
    
    Imagine...::
    
        >>> from fixture import DataSet
        >>> class PersonData(DataSet):
        ...     class adam:
        ...         father=None
        ...     class eve:
        ...         father=None
        ...     class jenny:
        ...         pass
        ...     jenny.father = adam
        ... 
    
    This would be a way to indicate that jenny's father is adam.  This class 
    will encapsulate that reference so it can be resolved as close to when it 
    was created as possible.
    
    """
    def __init__(self, dataset, key):
        self.dataset = dataset
        self.key = key
    
    def get_stored_object_from_loader(self, loader):
        loaded_ds = loader.loaded[self.dataset]
        return loaded_ds.meta._stored_objects.get_object(self.key)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
