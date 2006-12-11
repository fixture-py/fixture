
class DataContainer(object):
    _data = {}
    _keys = []
    
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

class DataRow(DataContainer):
    _data = {}
    
    def __init__(self, data):
        self._data = data
        self._keys = [k for k in data]
    
    def __iter__(self):
        for k in self._data:
            yield k
    
    def items(self):
        for k,v in self._data.items():
            yield (k,v)

class DataSet(DataContainer):
    """a set of dictionaries.
    
    each attribute/key is a dictionary.
    """
    _loader = None
    _storage = None
    _storage_medium = None
    _row = DataRow
    _data = {}
    
    def __init__(self):
        self._data = {}
        self._keys = []
        for key, data in self.data():
            if self._data.get(key, False):
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this already an attribute)" % key)
            self._keys.append(key)
            self._data[key] = self._row(data)
    
    def __iter__(self):
        for key in self._keys:
            yield (key, getattr(self, key))
    
    def data(self):
        """returns iterable key/dict pairs.
        
        >>> from fixture import DataSet
        >>> class flowers(DataSet):
        ...     data = (('violet', dict(color='blue')), 
        ...             ('rose', dict(color='red')))
        ... 
        >>> f = flowers()
        >>> f.violet
        {'color': 'blue'}
        >>> f.rose
        {'color': 'red'}
        
        
        >>> from fixture import DataSet
        >>> class flowers(DataSet):
        ...     def data(self):
        ...         return (('violet', dict(color='blue')), 
        ...                 ('rose', dict(color='red')))
        ... 
        >>> f = flowers()
        >>> f.violet
        {'color': 'blue'}
        >>> f.rose
        {'color': 'red'}
                     
        """
        raise NotImplementedError

class SuperSet(DataContainer):
    """a set of data sets.
    
    each attribute/key is a DataSet.
    """
    _data = {}
    def dataset_to_key(self, dataset):
        return dataset.__class__.__name__
        
    def __init__(self, *datasets):
        self._data = {}
        self._keys = []
        self._datasets = {}
        self._dataset_keys = []
        for d in datasets:
            k = self.dataset_to_key(d)
            self._keys.append(k)
            self._dataset_keys.append(k)
            self._data[k] = d
            self._datasets[k] = d
    
    def __iter__(self):
        for k in self._dataset_keys:
            yield self._datasets[k]

class MergedSuperSet(SuperSet):
    """a collection of data sets.
    
    all attributes of all data sets are merged together.
    """
    _data = {}
    def __init__(self, *datasets):
        # merge all datasets together ...
        self._data = {}
        self._keys = []
        self._datasets = {}
        self._dataset_keys = []
        self._keys_to_datasets = {}
        for dataset in datasets:
            dkey = self.dataset_to_key(dataset)
            self._dataset_keys.append(dkey)
            self._datasets[dkey] = dataset
            
            for k,row in dataset:
                if k in self._keys_to_datasets:
                    raise ValueError(
                        "cannot add key '%s' because it was "
                        "already added by %s" % (
                            k, self._keys_to_datasets[k]))
                self._keys.append(k)
                self._data[k] = row
                self._keys_to_datasets[k] = dataset
                