
from fixture import defaults

class DataSet(object):
    """a set of dictionaries.
    
    each attribute/key is a dictionary.
    """
    data = None
    loader = None
    
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