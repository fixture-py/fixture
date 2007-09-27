
"""Representation of Data

.. contents:: :local:

Before loading data, you need to define it. A single subclass of
DataSet represents a database relation in Python code. Think of the class as a
table, each inner class as a row, and each attribute per row as a column value.
For example::

    >>> from fixture import DataSet
    >>> class Authors(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"

The inner class ``frank_herbert`` defines a row with the columns ``first_name``
and ``last_name``. The name ``frank_herbert`` is an identifier that you can use
later on, when you want to refer to this specific row.

The main goal will be to load this data into something useful, like a database.
But notice that the ``id`` values aren't defined in the DataSet. This is because
the database will most likely create an ``id`` for you when you insert the row 
(however, if you need to specify a specific ``id`` number, you are free to do 
so).  How you create a DataSet will be influenced by how the underlying data object saves data.

Inheriting DataSet rows
~~~~~~~~~~~~~~~~~~~~~~~

Since a row is just a Python class, you can inherit from a row to morph its values, i.e.::

    >>> class Authors(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"
    ...     class brian_herbert(frank_herbert):
    ...         first_name = "Brian"

This is useful for adhering to the DRY principle (Don't Repeat Yourself) as well
as for `testing edge cases`_.

.. note::
    The primary key value will not be inherited from a row.  See 
    `Customizing a DataSet`_ if you need to set the name of a DataSet's primary 
    key to something other than ``id``.

Referencing foreign DataSet classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When defining rows in a DataSet that reference foreign keys, you need to mimic how your data object wants to save such a reference.  If your data object wants to save foreign keys as objects (not ID numbers) then you can simply reference another row in a DataSet as if it were an object.::

    >>> class Books(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author = Authors.frank_herbert
    ...     class sudanna:
    ...         title = "Sudanna Sudanna"
    ...         author = Authors.brian_herbert

During data loading, the reference to DataSet ``Authors.brian_herbert`` will be replaced with the actual stored object used to load that row into the database.  This will work as expected for one-to-many relationships, i.e.::

    >>> class Books(DataSet):
    ...     class two_worlds:
    ...         title = "Man of Two Worlds"
    ...         authors = [Authors.frank_herbert, Authors.brian_herbert]

However, in some cases you may need to reference an attribute that does not have a value until it is loaded, like a serial ID column.  (Note that this is not supported by the `sqlalchemy`_ data layer when using sessions.)  To facilitate this, each inner class of a DataSet gets decorated with a special method, ``ref()``,
that can be used to reference a column value before it exists, i.e.::

    >>> class Books(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author_id = Authors.frank_herbert.ref('id')
    ...     class sudanna:
    ...         title = "Sudanna Sudanna"
    ...         author_id = Authors.brian_herbert.ref('id')

This sets the ``author_id`` to the ``id`` of another row in ``Author``, as if it
were a foreign key. But notice that the ``id`` attribute wasn't explicitly
defined by the ``Authors`` data set. When the ``id`` attribute is accessed later
on, its value is fetched from the actual row inserted.

Customizing a Dataset
~~~~~~~~~~~~~~~~~~~~~

A DataSet can be customized by defining a special inner class named ``Meta``.
See the `DataSet.Meta`_ API for more info.

.. _DataSet.Meta: ../apidocs/fixture.dataset.DataSet.Meta.html
.. _testing edge cases: http://brian.pontarelli.com/2006/12/04/the-importance-of-edge-case-testing/

.. api_only::
   The fixture.dataset module
   ~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import sys, types
from fixture.util import ObjRegistry

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
    """A reference to a row in a DataSet class.
    
    This allows a DataSet to reference an id column of a "foreign key" DataSet 
    before it exists.
    
    Ref is a Descriptor containing a deferred value to an attribute of a data 
    object (like an instance of a SQLAlchemy mapped class).  It provides the 
    DataSet a way to cloak the fact that "id" is an attribute only populated 
    after said data object is saved to the database.  In other words, the 
    DataSet doesn't know or care when it has been loaded or not.  It thinks it 
    is referencing "id" all the same.  The timing of when id is accessed is 
    handled by the LoadableFixture.
    
    """
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
        # store a backref to the container dataset
        row._dataset = cls
        
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
            

def is_rowlike(candidate):
    """returns True if candidate is *like* a DataRow.
    
    Not to be confused with issubclass(candidate, DataRow).
    
    A regular or new-style class is row-like because DataSet objects allow any 
    type of class to declare a row of data
    """
    return hasattr(candidate, '_dataset') and type(candidate._dataset) in (
                                                            DataType, DataSet)

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
    """defines data to be loaded
    
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
    
    Keyword Arguments
    -----------------
    - default_refclass
  
      - a SuperSet to use if None has already been specified in Meta

    Special inner Meta class
    ------------------------
    
    See DataSet.Meta for details
    
    """
    __metaclass__ = DataType
    _reserved_attr = DataContainer._reserved_attr + ('data', 'shared_instance')
    ref = None
    class Meta(DataContainer.Meta):
        """configures a DataSet class.
        
        The inner class Meta is used to configure a DataSet .  The following are 
        acknowledged attributes:

        storable
            an object that should be used to store this DataSet.  If omitted the 
            loader's style object will look for a storable object in its env, 
            using storable_name

        storable_name
            the name of the storable object that the loader should fetch from 
            its env to load this DataSet with.  If omitted, the loader's style 
            object will try to guess the storable_name based on its env and the 
            name of the DataSet class

        primary_key
            this is a list of names that should be acknowledged as primary keys 
            in a DataSet.  The default is simply ['id'].
        """
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
        
        def mkref():
            clean_refs = []
            for ds in iter(self.meta.references):
                if ds is type(self):
                    # whoops
                    continue
                clean_refs.append(ds)
            self.meta.references = clean_refs
            
            return default_refclass(*[
                ds.shared_instance(default_refclass=default_refclass) 
                    for ds in iter(self.meta.references)
            ])
        
        # data def style classes, so they have refs before data is walked
        if len(self.meta.references) > 0:
            self.ref = mkref()
            
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
            self.ref = mkref()
    
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
        
        def add_ref_from_rowlike(rowlike):
            if rowlike._dataset not in self.meta.references:
                self.meta.references.append(rowlike._dataset)
                    
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
                    # the .ref attribute
                    continue
                elif type(col_val) in (types.ListType, types.TupleType):
                    for c in col_val:
                        if is_rowlike(c):
                            add_ref_from_rowlike(c)
                        else:
                            raise TypeError(
                                "multi-value columns can only contain "
                                "rowlike objects, not %s of type %s" % (
                                                col_val, type(col_val)))
                elif is_rowlike(col_val):
                    add_ref_from_rowlike(col_val)
                elif isinstance(col_val, Ref.Value):
                    ref = col_val.ref
                    if ref.dataset_class not in self.meta.references:
                        # store the reference:
                        self.meta.references.append(ref.dataset_class)
                    
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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    