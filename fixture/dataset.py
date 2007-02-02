
"""representations of data."""

from fixture.util import ObjRegistry

class DataContainer(object):
    """contains data accessible by attribute and/or key.
    
    for all internally used attributes, use the inner class Meta.
    """
    class Meta:
        data = None
        keys = None
        
    def __init__(self, data=None, keys=None):
        if not hasattr(self, 'meta'):
            self.meta = self.Meta()
        if not data: 
            data = {}
        self.meta.data = data
        if not keys: 
            keys = []
        self.meta.keys = keys
    
    def __getitem__(self, key):
        return self.meta.data[key]
        
    def __getattr__(self, name):
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

class DataRow(DataContainer):
    """a key/attribute accessible dictionary."""
    class Meta(DataContainer.Meta):
        pass
    
    def __init__(self, data):
        DataContainer.__init__(self, data=data, keys=[k for k in data])
    
    def __iter__(self):
        for k in self.meta.data:
            yield k
    
    def iteritems(self):
        for k,v in self.meta.data.items():
            yield (k,v)
    
    def items(self):
        for k,v in self.iteritems():
            yield (k,v)

class DataSetContainer(object):
    """yields datasets when itered over."""
    class Meta:
        datasets = None
        dataset_keys = None
        
    def __init__(self):
        if not hasattr(self, 'meta'):
            self.meta = self.Meta()
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
    
    all attributes of all data sets are merged together.
    """
    class Meta(SuperSet.Meta):
        pass
    def __init__(self, *datasets):
        if not hasattr(self, 'meta'):
            self.meta = self.Meta()
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
                self._setdata(k, row)
                self.meta.keys_to_datasets[k] = dataset 
    
    def _store_datasets(self, datasets):    
        for dataset in datasets:
            self._setdataset(dataset)
            
            for d in dataset.ref:
                self._setdataset(d, isref=True)

class DataSet(DataContainer):
    """a set of row objects.
    
    a loader will typically want to load a dataset into a 
    single storage medium.  I.E. a table in a database.
    
    >>> from fixture import DataSet
    >>> class Flowers(DataSet):
    ...     def data(self):
    ...         return (
    ...             ('violets', dict(color='blue')), 
    ...             ('roses', dict(color='red')))
    ... 
    >>> f = Flowers()
    >>> f.violets.color
    'blue'
    >>> f.violets['color']
    'blue'
    >>> for key, row in f:
    ...     print key, 'are', row.color
    ... 
    violets are blue
    roses are red
    
    """
    ref = None
    class Meta(DataContainer.Meta):
        loader = None
        storage = None
        storage_medium = None
        stored_objects = []
        requires = []
        references = []
        row = DataRow
        refclass = SuperSet
    
    def __init__(self):
        DataContainer.__init__(self)
        
        # we want the convenience of not having to 
        # inherit DataSet.Meta.  hmmm ...
        if not isinstance(self.meta, DataSet.Meta):
            defaults = DataSet.Meta()
            for name in dir(defaults):
                if not hasattr(self.meta, name):
                    setattr(self.meta, name, getattr(defaults, name))
        
        self.meta.stored_objects = []
        
        self.ref = self.meta.refclass(*(
            [s() for s in iter(self.meta.requires)] + 
            [s() for s in iter(self.meta.references)] ))
        
        for key, data in self.data():
            if hasattr(self, key):
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this is already an attribute)" % key)
            self._setdata(key, self.meta.row(data))
    
    def __iter__(self):
        for key in self.meta.keys:
            yield (key, getattr(self, key))
    
    def data(self):
        """returns iterable key/dict pairs.                     
        """
        raise NotImplementedError
                