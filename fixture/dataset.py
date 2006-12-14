
class DataContainer(object):
    """contains data accessible by attribute and/or key.
    
    names/keys starting with an underscore are reserved for internal use.
    """
    class Config:
        data = None
        keys = None
        
    def __init__(self, data=None, keys=None):
        if not hasattr(self, 'conf'):
            self.conf = self.Config()
        if not data: 
            data = {}
        self.conf.data = data
        if not keys: 
            keys = []
        self.conf.keys = keys
    
    def __getitem__(self, key):
        return self.conf.data[key]
        
    def __getattr__(self, name):
        try:
            return self.conf.data[name]
        except KeyError:
            raise AttributeError("%s has no attribute '%s'" % (self, name))
    
    def __repr__(self):
        if hasattr(self, 'conf'):
            keys = self.conf.keys
        else:
            keys = None
        return "<%s at %s with keys %s>" % (
                self.__class__.__name__, 
                hex(id(self)), keys)
    
    def _setdata(self, key, value):
        self.conf.keys.append(key)
        self.conf.data[key] = value

class DataRow(DataContainer):
    """a key/attribute accessible dictionary."""
    class Config(DataContainer.Config):
        pass
    def __init__(self, data):
        DataContainer.__init__(self, data=data, keys=[k for k in data])
    
    def __iter__(self):
        for k in self.conf.data:
            yield k
    
    def items(self):
        for k,v in self.conf.data.items():
            yield (k,v)

class DataSetContainer(object):
    """yields datasets when itered over."""
    class Config:
        datasets = None
        dataset_keys = None
        
    def __init__(self):
        if not hasattr(self, 'conf'):
            self.conf = self.Config()
        self.conf.datasets = {}
        self.conf.dataset_keys = []
        self.conf._cache = {}
    
    def __iter__(self):
        for k in self.conf.dataset_keys:
            yield self.conf.datasets[k]
        
    def _dataset_to_key(self, dataset):
        return dataset.__class__.__name__
        
    def _setdataset(self, dataset, key=None, isref=False):
        
        # due to reference resolution we might get colliding data sets...
        cache_id = id(dataset.__class__)
        if cache_id in self.conf._cache:
            return False
            
        if key is None:
            key = self._dataset_to_key(dataset)
        if not isref:
            # refs are not yielded
            self.conf.dataset_keys.append(key)
            
        self.conf.datasets[key] = dataset
        self.conf._cache[cache_id] = 1
        return True

class SuperSet(DataContainer, DataSetContainer):
    """a set of data sets.
    
    each attribute/key is a DataSet.
    """
    class Config(DataContainer.Config, DataSetContainer.Config):
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
    class Config(SuperSet.Config):
        pass
    def __init__(self, *datasets):
        if not hasattr(self, 'conf'):
            self.conf = self.Config()
        self.conf.keys_to_datasets = {}
        SuperSet.__init__(self, *datasets)
    
    def _setdataset(self, dataset, key=None, isref=False):
        if SuperSet._setdataset(self, dataset, key=key, isref=isref):
            for k,row in dataset:
                if k in self.conf.keys_to_datasets:
                    raise ValueError(
                        "cannot add key '%s' for %s because it was "
                        "already added by %s" % (
                            k, dataset, self.conf.keys_to_datasets[k]))
                self._setdata(k, row)
                self.conf.keys_to_datasets[k] = dataset 
    
    def _store_datasets(self, datasets):    
        for dataset in datasets:
            self._setdataset(dataset)
            
            for d in dataset.ref:
                self._setdataset(d, isref=True)

class DataSet(DataContainer):
    """a set of row objects."""
    ref = None
    class Config(DataContainer.Config):
        loader = None
        storage = None
        storage_medium = None
        requires = []
        references = []
        row = DataRow
        refclass = SuperSet
    
    def __init__(self):
        DataContainer.__init__(self)
        
        # we want the convenience of not having to 
        # inherit DataSet.Config.  hmmm ...
        if not isinstance(self.conf, DataSet.Config):
            defaults = DataSet.Config()
            for name in dir(defaults):
                if not hasattr(self.conf, name):
                    setattr(self.conf, name, getattr(defaults, name))
        
        self.ref = self.conf.refclass(*(
            [s() for s in self.conf.requires] + 
            [s() for s in self.conf.references] ))
        
        for key, data in self.data():
            if hasattr(self, key):
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this is already an attribute)" % key)
            self._setdata(key, self.conf.row(data))
    
    def __iter__(self):
        for key in self.conf.keys:
            yield (key, getattr(self, key))
    
    def data(self):
        """returns iterable key/dict pairs.
        
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
        raise NotImplementedError
                