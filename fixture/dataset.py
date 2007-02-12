
"""representations of data."""

import sys
from fixture.util import ObjRegistry
import types

__all__ = ['DataSet']

class DataContainer(object):
    """contains data accessible by attribute and/or key.
    
    for all internally used attributes, use the inner class Meta.
    On instances, use self.meta instead.
    """
    _reserved_attr = ('meta', 'Meta', 'ref', 'get')
    class Meta:
        data = None
        keys = None
        
    def __init__(self, data=None, keys=None):
        lazy_meta(self)
        if not data: 
            data = {}
        self.meta.data = data
        if not keys: 
            keys = []
        self.meta.keys = keys
    
    def __contains__(self, name):
        return name in self.meta.keys
    
    def __getitem__(self, key):
        return self.meta.data[key]
        
    def __getattribute__(self, name):
        
        # it is necessary to completely override __getattr__
        # so that class attributes don't interfer
        if name.startswith('_') or name in self._reserved_attr:
            return object.__getattribute__(self, name)
        try:
            return self.meta.data[name]
        except KeyError:
            raise AttributeError("%s has no attribute '%s'" % (self, name))
    
    def __repr__(self):
        if hasattr(self, 'meta'):
            keys = self.meta.keys
        else:
            keys = None
        return "<%s at %s with keys %s>" % (
                self.__class__.__name__,
                hex(id(self)), keys)
    
    def get(self, k, default=None):
        return self.meta.data.get(k, default)
    
    def _setdata(self, key, value):
        if key not in self.meta.data:
            self.meta.keys.append(key)
        self.meta.data[key] = value
        

class Ref(object):
    """A reference to a row in a DataSet class."""
    class Value(object):
        """A reference to a value in a row of a DataSet class."""
        def __init__(self, ref, attr_name):
            self.attr_name = attr_name
            self.ref = ref
        
        def __repr__(self):
            return "<%s.%s for %s.%s.%s (%s)>" % (
                Ref.__name__, self.__class__.__name__,
                self.ref.dataset_class.__name__, self.ref.key, self.attr_name,
                (self.ref.dataset_obj is None and 'not yet loaded' or 'loaded'))
    
        def __get__(self, obj, type=None):
            if obj is None:
                # self was assigned to a class object
                return self
            else:
                # self was assigned to an instance
                if self.ref.dataset_obj is None:
                    raise RuntimeError(
                        "Cannot access %s, referenced %s %s has not "
                        "been loaded yet" % (
                            self, DataSet.__name__, self.ref.dataset_class))
                obj = self.ref.dataset_obj.meta._stored_objects.get_object(
                                                                self.ref.key)
                return getattr(obj, self.attr_name)
                # raise ValueError("called __get__(%s, %s)" % (obj, type))
            
    def __init__(self, dataset_class, row):
        self.dataset_class = dataset_class
        self.dataset_obj = None
        self.row = row
        # i.e. the name of the row class...
        self.key = self.row.__name__
    
    def __call__(self, ref_name):
        return self.Value(self, ref_name)
    
    def __repr__(self):
        return "<%s to %s.%s at %s>" % (
            self.__class__.__name__, self.dataset_class.__name__, 
            self.row.__name__, hex(id(self)))

def is_row_class(attr):
    attr_type = type(attr)
    return ((attr_type==types.ClassType or attr_type==type) and 
                attr.__name__ != 'Meta' and 
                not issubclass(attr, DataContainer.Meta))
    
class DataType(type):
    """meta class for creating DataSet classes."""
    default_primary_key = ['id']
                    
    def __init__(cls, name, bases, cls_attr):
        super(DataType, cls).__init__(name, bases, dict)
        
        if 'Meta' in cls_attr and hasattr(cls_attr['Meta'], 'primary_key'):
            cls_attr['_primary_key'] = cls_attr['Meta'].primary_key
        else:
            cls_attr['_primary_key'] = cls.default_primary_key
        
        # just like dir(), we should do this in alpha order :
        ## NOTE: dropping support for <2.4 here...
        for name in sorted(cls_attr.keys()):
            attr = cls_attr[name]
            if is_row_class(attr):
                cls.decorate_row(attr, name, bases, cls_attr)
                
        del cls_attr['_primary_key']
    
    def decorate_row(cls, row, name, bases, cls_attr):
        # bind a ref method
        row.ref = Ref(cls, row)
        
        # fix inherited primary keys
        names_to_uninherit = []
        for name in dir(row):
            if name in cls_attr['_primary_key']:
                if name not in row.__dict__:
                    # then this was an inherited value, so we need to nullify it 
                    # without 1) disturbing the other inherited values and 2) 
                    # disturbing the inherited class.  is this nuts?
                    names_to_uninherit.append(name)
        bases_to_replace = []
        if names_to_uninherit:
            base_pos = 0
            for c in row.__bases__:
                for name in names_to_uninherit:
                    if name in c.__dict__:
                        bases_to_replace.append((c, base_pos))
                        # just need to detect one attribute...
                        break
                base_pos += 1
        new_bases = [b for b in row.__bases__]
        for base_c, base_pos in bases_to_replace:
            # this may not work if the row's base was a new-style class
            new_base = types.ClassType(
                            base_c.__name__, base_c.__bases__, 
                            dict([(k, getattr(base_c, k)) for k in dir(base_c) \
                                    if not k.startswith('_') and \
                                    k not in names_to_uninherit]))
            new_bases[base_pos] = new_base
        if new_bases:
            row.__bases__ = tuple(new_bases)
            
                    

class DataRow(object):
    """a DataSet row, values accessible by attibute or key."""
    _reserved_attr = ('columns',)
    
    def __init__(self, dataset):
        object.__setattr__(self, '_dataset', dataset)
        # i.e. the name of the row class...
        object.__setattr__(self, '_key', self.__class__.__name__)
    
    def __getitem__(self, item):
        return getattr(self, item)
    
    def __getattr__(self, name):
        # an undefined data attribute was referenced,
        # let's look for it in the stored object.
        # an example of this would be an ID, which was
        # created only after load
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        
        obj = self._dataset.meta._stored_objects.get_object(self._key)
        return getattr(obj, name)
    
    @classmethod
    def columns(self):
        for k in dir(self):
            if k.startswith('_') or k in self._reserved_attr:
                continue
            yield k
    
    def __setattr__(self, name, val):
        raise AttributeError("cannot set attributes on a %s instance" % (
                                                self.__class__.__name__))

class DataSetStore(list):
    """keeps track of actual objects stored in a dataset."""
    def __init__(self, dataset):
        list.__init__(self)
        self.dataset = dataset
        self._ds_key_map = {}
    
    def get_object(self, key):
        """returns the object at this key.
        
        In this example...
        
            >>> class EventData(DataSet):
            ...     class click:
            ...         id=1
            
        ...the key is "click."  The object returned would be an adapter for 
        EventData, probably an Event object
        
        """
        try:
            return self[ self._ds_key_map[key] ]
        except (IndexError, KeyError):
            etype, val, tb = sys.exc_info()
            raise etype("row '%s' hasn't been loaded for %s (loaded: %s)" % (
                                        key, self.dataset, self)), None, tb
        
    def store(self, key, obj):
        self.append(obj)
        pos = len(self)-1
        self._ds_key_map[key] = pos

dataset_registry = ObjRegistry()

class DataSet(DataContainer):
    """a set of row objects.
    
    Keyword Arguments
    -----------------
    - default_refclass
      
      - a SuperSet to use if None has already been specified in Meta
    
    special inner Meta class
    ------------------------
    
    The inner class Meta is used to configure a DataSet.  The following are 
    acknowledged attributes:
    
    - storable
    
      - an object that should be used to store this DataSet.  If omitted the 
        loader's style object will look for a storable object in its env, using 
        storable_name
    
    - storable_name
    
      - the name of the storable object that the loader should fetch from its 
        env to load this DataSet with.  If omitted, the loader's style object 
        will try to guess the storable_name based on its env and the name of the 
        DataSet class
    
    - primary_key
    
      - this is a list of names that should be acknowledged as primary keys in a 
        DataSet.  The default is simply ['id'] but only comes into affect for 
        inherited values.  In this default configuration, a row cannot inherit 
        another rows primary key attributes.
    
    a loader will typically want to load a dataset into a 
    single storage medium.  I.E. a table in a database.
    
    Note that rows are always classes until the dataset instance has been 
    loaded::
    
        >>> class Flowers(DataSet):
        ...     class violets:
        ...         color = 'blue'
        ...     class roses:
        ...         color = 'red'
        ... 
        >>> f = Flowers()
        >>> f.violets.color
        'blue'
    
    Row values can also be inherited from other rows, just as normal inheritance 
    works in Python.  See the primary_key Meta attribute above for how 
    inheritance works on primary keys::
    
        >>> class Recipes(DataSet):
        ...     class chowder:
        ...         is_soup = True
        ...         name = "Clam Chowder"
        ...     class tomato_bisque(chowder):
        ...         name = "Tomato Bisque"
        ... 
        >>> r = Recipes()
        >>> r.chowder.is_soup
        True
        >>> r.tomato_bisque.is_soup
        True
    
    """
    __metaclass__ = DataType
    _reserved_attr = DataContainer._reserved_attr + ('data', 'shared_instance')
    ref = None
    class Meta(DataContainer.Meta):
        row = DataRow
        storable = None
        storable_name = None
        storage_medium = None
        primary_key = [k for k in DataType.default_primary_key]
        references = []
        _stored_objects = None
        _built = False
    
    def __init__(self, default_refclass=None, default_meta=None):
        DataContainer.__init__(self)
        
        # we want the convenience of not having to 
        # inherit DataSet.Meta.  hmmm ...
        if not default_meta:
            default_meta = DataSet.Meta
        if not isinstance(self.meta, default_meta):
            defaults = default_meta()
            for name in dir(defaults):
                if not hasattr(self.meta, name):
                    setattr(self.meta, name, getattr(defaults, name))
        
        self.meta._stored_objects = DataSetStore(self)
        # dereference from class ...        
        try:
            cl_attr = getattr(self.Meta, 'references')
        except AttributeError:
            cl_attr = []
        setattr(self.meta, 'references', [c for c in cl_attr])
        
        if not default_refclass:
            default_refclass = SuperSet
        
        def mkref(references):
            return default_refclass(*[
                        ds.shared_instance(default_refclass=default_refclass) \
                            for ds in iter(references)])
        
        # data def style classes, so they have refs before data is walked
        if len(self.meta.references) > 0:
            self.ref = mkref(self.meta.references)
            
        for key, data in self.data():
            if key in self:
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this is already an attribute)" % key)
                    
            if isinstance(data, dict):
                # make a new class object for the row data
                # so that a loaded dataset can instantiate this...
                data = type(key, (self.meta.row,), data)
            self._setdata(key, data)
            
        if not self.ref:
            # type style classes, since refs were discovered above
            self.ref = mkref(self.meta.references)
    
    def __iter__(self):
        for key in self.meta.keys:
            yield (key, getattr(self, key))
    
    def data(self):
        """returns iterable key/dict pairs.
        
        You would only need to override this if you have a DataSet that will 
        break unless it is ordered very specifically.  Since class-style DataSet 
        objects are just classes with attributes, its rows will be loaded in 
        alphabetical order.  The alternative is to define a DataSet as follows.  
        However, note that this is not as functional as a class-style DataSet::
        
            >>> class Birds(DataSet):
            ...     def data(self):
            ...         return (
            ...             ('blue_jay', dict(
            ...                 name="Blue Jay")),
            ...             ('crow', dict(
            ...                 name="Crow")),)
            ... 
            >>> b = Birds()
            >>> b.blue_jay.name
            'Blue Jay'
            >>> b.crow.name
            'Crow'
            
        """
        if self.meta._built:
            for k,v in self:
                yield (k,v)
                
        def public_dir(obj):
            for name in dir(obj):
                if name.startswith("_"):
                    continue
                yield name
                
        empty = True
        for name in public_dir(self.__class__):
            val = getattr(self.__class__, name)
            if not is_row_class(val):
                continue
            
            empty = False
            key = name
            row_class = val
            row = {}
            
            for col_name in public_dir(row_class):
                col_val = getattr(row_class, col_name)
                
                if isinstance(col_val, Ref):
                    continue
                if isinstance(col_val, Ref.Value):
                    ref = col_val.ref
                    if ref.dataset_class not in self.meta.references:
                        # store the reference:
                        self.meta.references.append(ref.dataset_class)
                        
                    ### FIXME: with __get__ this will
                    ### just be the Ref.Value object ...
                    # col_val = getattr(ref.row, col_val.attr_name)
                    
                row[col_name] = col_val
            yield (key, row)
            
        if empty:
            raise ValueError("cannot create an empty DataSet")
        self.meta._built = True
    
    @classmethod
    def shared_instance(cls, **kw):
        # fixme: default_refclass might be in **kw.  But only a loader can set a 
        # refclass.  hmm
        if cls in dataset_registry:
            dataset = dataset_registry[cls]
        else:
            dataset = cls(**kw)
            dataset_registry.register(dataset)
        return dataset

class DataSetContainer(object):
    """yields datasets when itered over."""
    class Meta:
        datasets = None
        dataset_keys = None
        
    def __init__(self):
        lazy_meta(self)
        self.meta.datasets = {}
        self.meta.dataset_keys = []
        self.meta._cache = ObjRegistry()
    
    def __iter__(self):
        for k in self.meta.dataset_keys:
            yield self.meta.datasets[k]
        
    def _dataset_to_key(self, dataset):
        return dataset.__class__.__name__
        
    def _setdataset(self, dataset, key=None, isref=False):
        
        # due to reference resolution we might get colliding data sets...
        if dataset in self.meta._cache:
            return False
            
        if key is None:
            key = self._dataset_to_key(dataset)
        if not isref:
            # refs are not yielded
            self.meta.dataset_keys.append(key)
            
        self.meta.datasets[key] = dataset
        
        self.meta._cache.register(dataset)
        return True

class SuperSet(DataContainer, DataSetContainer):
    """a set of data sets.
    
    each attribute/key is a DataSet.
    """
    class Meta(DataContainer.Meta, DataSetContainer.Meta):
        pass
        
    def __init__(self, *datasets):
        DataContainer.__init__(self)
        DataSetContainer.__init__(self)
        self._store_datasets(datasets)
    
    def _store_datasets(self, datasets):
        for d in datasets:
            k = self._dataset_to_key(d)
            self._setdata(k, d)
            self._setdataset(d, key=k)
            
            for ref_d in d.ref:
                k = self._dataset_to_key(ref_d)
                self._setdata(k, ref_d)
                self._setdataset(ref_d, key=k, isref=True)

class MergedSuperSet(SuperSet):
    """a collection of data sets.
    
    all attributes of all data sets are merged together so that they are 
    accessible in this class, independent of dataset.  duplicate attribute 
    names are not allowed
    """
    class Meta(SuperSet.Meta):
        pass
    def __init__(self, *datasets):
        lazy_meta(self)
        self.meta.keys_to_datasets = {}
        SuperSet.__init__(self, *datasets)
    
    def _setdataset(self, dataset, key=None, isref=False):
        if SuperSet._setdataset(self, dataset, key=key, isref=isref):
            for k,row in dataset:
                if k in self.meta.keys_to_datasets:
                    raise ValueError(
                        "cannot add key '%s' for %s because it was "
                        "already added by %s" % (
                            k, dataset, self.meta.keys_to_datasets[k]))
                
                # need an instance here, if it's a class...
                if not isinstance(row, DataRow):
                    row = row(dataset)
                self._setdata(k, row)
                self.meta.keys_to_datasets[k] = dataset 
    
    def _store_datasets(self, datasets):
        for dataset in datasets:
            self._setdataset(dataset)
            
            for d in dataset.ref:
                self._setdataset(d, isref=True)
                

def lazy_meta(obj):
    if not hasattr(obj, 'meta'):
        setattr(obj, 'meta', obj.Meta())
        