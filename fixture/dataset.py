
from fixture import defaults

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
    
    def items(self):
        for k,v in self.__dict__.items():
            yield (k,v)

class DataSet(object):
    """a set of dictionaries.
    
    each attribute/key is a dictionary.
    """
    data = None
    loader = None
    row = DataRow
    
    def __init__(self):
        for key, data in self.data():
            if self.__dict__.get(key, False):
                raise ValueError(
                    "data() cannot redeclare key '%s' "
                    "(this already an attribute)" % key)
            self.__dict__[key] = self.row(data)
    
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

class SuperSet(object):
    """a set of data sets.
    
    each attribute/key is a DataSet.
    """
    def __init__(self, *datasets):
        self.datasets = datasets

class MergedSuperSet(object):
    """a collection of data sets.
    
    all attributes of all data sets are merged together.
    """
    pass