
class DataContainer(object):
    """contains data accessible by attribute and/or key.
    
    names/keys starting with an underscore are reserved for internal use.
    """
    def __init__(self, data=None, keys=None):
        if not data: 
            data = {}
        self._data = data
        if not keys: 
            keys = []
        self._keys = keys
    
    def __getitem__(self, key):
        return self._data[key]
        
    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError("%s has no attribute '%s'" % (self, name))
    
    def __repr__(self):
        return "<%s at %s with keys %s>" % (
                self.__class__.__name__, hex(id(self)), self._keys)
    
    def _setdata(self, key, value):
        self._keys.append(key)
        self._data[key] = value

class DataRow(DataContainer):
    """a key/attribute accessible dictionary."""
    def __init__(self, data):
        DataContainer.__init__(self, data=data, keys=[k for k in data])
    
    def __iter__(self):
        for k in self._data:
            yield k
    
    def items(self):
        for k,v in self._data.items():
            yield (k,v)

class DataSet(DataContainer):
    """a set of row objects."""
    _loader = None
    _storage = None
    _storage_medium = None
    _row = DataRow
    
    def __init__(self):
        DataContainer.__init__(self)
        for key, data in self.data():
            if hasattr(self, key):
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this is already an attribute)" % key)
            self._setdata(key, self._row(data))
    
    def __iter__(self):
        for key in self._keys:
            yield (key, getattr(self, key))
    
    def data(self):
        """returns iterable key/dict pairs.
        
        >>> from fixture import DataSet
        >>> class flowers(DataSet):
        ...     def data(self):
        ...         return (
        ...             ('violet', dict(color='blue')), 
        ...             ('rose', dict(color='red')))
        ... 
        >>> f = flowers()
        >>> f.violet.color
        'blue'
        >>> f.violet['color']
        'blue'
        >>> f.rose.color
        'red'
                     
        """
        raise NotImplementedError

class DataSetContainer(object):
    """yields datasets when itered over."""
    def __init__(self):
        self._datasets = {}
        self._dataset_keys = []
    
    def __iter__(self):
        for k in self._dataset_keys:
            yield self._datasets[k]
        
    def _dataset_to_key(self, dataset):
        return dataset.__class__.__name__
        
    def _setdataset(self, dataset, key=None):
        if key is None:
            key = self._dataset_to_key(dataset)
        self._dataset_keys.append(key)
        self._datasets[key] = dataset

class SuperSet(DataContainer, DataSetContainer):
    """a set of data sets.
    
    each attribute/key is a DataSet.
    """
        
    def __init__(self, *datasets):
        DataContainer.__init__(self)
        DataSetContainer.__init__(self)
        self._store_datasets(datasets)
    
    def _store_datasets(self, datasets):
        for d in datasets:
            k = self._dataset_to_key(d)
            self._setdata(k, d)
            self._setdataset(d, key=k)

class MergedSuperSet(SuperSet):
    """a collection of data sets.
    
    all attributes of all data sets are merged together.
    """
    def __init__(self, *datasets):
        self._keys_to_datasets = {}
        SuperSet.__init__(self, *datasets)
    
    def _store_datasets(self, datasets):
        for dataset in datasets:
            self._setdataset(dataset)
            
            for k,row in dataset:
                if k in self._keys_to_datasets:
                    raise ValueError(
                        "cannot add key '%s' because it was "
                        "already added by %s" % (
                            k, self._keys_to_datasets[k]))
                self._setdata(k, row)
                self._keys_to_datasets[k] = dataset
                