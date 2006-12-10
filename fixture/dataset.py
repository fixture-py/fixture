
class DataRow(object):
    def __init__(self, data):
        self.__dict__ = data
    
    def __getitem__(self, key):
        return self.__dict__[key]
        
    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError("%s %s has no attribute '%s'" % (
                                    self.__class__.__name__, self, name))
    
    def __iter__(self):
        for k in self.__dict__:
            yield k
    
    def __repr__(self):
        return "<%s at %s for %s>" % (
                self.__class__.__name__, hex(id(self)), self.__dict__)
    
    def items(self):
        for k,v in self.__dict__.items():
            yield (k,v)

class DataSetAccessor(object):
    """iterface for for DataSet-like objects."""
    def __getattr__(self, key):
        """self.key returns a dict for 'key'"""
        raise NotImplementedError
    
    def __getitem__(self, key):
        """self['key'] returns a dict for 'key'"""
        raise NotImplementedError
    
    def __iter__(self):
        """yield (key, dict) pairs, in order."""
        raise NotImplementedError

class DataSet(DataSetAccessor):
    """a set of dictionaries.
    
    each attribute/key is a dictionary.
    """
    data = None
    loader = None
    row = DataRow
    
    def __init__(self):
        self.keys = []
        for key, data in self.data():
            if self.__dict__.get(key, False):
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this already an attribute)" % key)
            self.keys.append(key)
            self.__dict__[key] = self.row(data)
    
    def __iter__(self):
        for key in self.keys:
            yield (key, getattr(self, key))
    
    def __getitem__(self, k):
        return self.__dict__[k]
    
    def __repr__(self):
        return "<%s at %s for %s>" % (
                self.__class__.__name__, hex(id(self)), self.__dict__)
    
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

class SuperSetAccessor(object):
    """iterface for for SuperSet-like objects."""
    def __getattr__(self, key):
        """self.key returns a DataSet for 'key'."""
        raise NotImplementedError
    
    def __getitem__(self, key):
        """self['key'] returns a DataSet for 'key'."""
        raise NotImplementedError
    
    def __iter__(self):
        """yields (key, DataSet) pairs, in order."""
        raise NotImplementedError

class SuperSet(SuperSetAccessor):
    """a set of data sets.
    
    each attribute/key is a DataSet.
    """
    def dataset_to_key(self, dataset):
        return dataset.__class__.__name__
    
    def __getattr__(self, key):
        return self.datasets[key]
    
    def __getitem__(self, key):
        return self.datasets[key]
        
    def __init__(self, *datasets):
        self.datasets = {}
        self.keys = []
        for d in datasets:
            k = self.dataset_to_key(d)
            self.keys.append(k)
            self.datasets[k] = d
    
    def __iter__(self):
        for k in self.keys:
            yield (k, self.datasets[k])

class MergedSuperSet(SuperSet, DataSetAccessor):
    """a collection of data sets.
    
    all attributes of all data sets are merged together.
    """        
    def __init__(self, *datasets):
        # merge all datasets together ...
        self.datasets = {}
        self.keys_to_datasets = {}
        self.keys = []
        for dataset in datasets:
            dkey = self.dataset_to_key(dataset)
            
            for k,row in dataset:
                if k in self.keys_to_datasets:
                    raise ValueError(
                        "cannot add key '%s' because it was "
                        "already added by %s" % (
                            k, self.keys_to_datasets[k]))
                self.keys.append(k)
                self.datasets[k] = row
                self.keys_to_datasets[k] = dataset
                