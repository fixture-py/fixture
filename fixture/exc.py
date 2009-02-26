
"""Fixture exceptions"""

class UninitializedError(Exception):
    pass

class DataSetActionException(Exception):
    """
    An exception while performing some action with a DataSet.
    
    In addtion to ``etype`` and ``val`` adds these properties:
    
    ``dataset``
        :class:`DataSet <fixture.dataset.DataSet>` that caused the exception
        
    ``key``
        Key on DataSet row if there is one
        
    ``row``
        :class:`DataRow <fixture.dataset.DataRow>` if there is one
        
    ``stored_object``
        Stored object if there is one
        
    used by :mod:`fixture.loadable` classes
    """
    def __init__(self, etype, val, dataset, 
                        key=None, row=None, stored_object=None):
        msg = "in %s" % dataset
        if key or row:
            msg = "with '%s' of '%s' %s" % (key, row, msg)
        elif stored_object:
            msg = "with %s %s" % (stored_object, msg)
        
        Exception.__init__(self, "%s: %s (%s)" % (etype.__name__, val, msg))
        
class LoadError(DataSetActionException):
    """
    An exception while loading data in DataSet.
    
    used by :mod:`fixture.loadable` classes
    """
    pass
class UnloadError(DataSetActionException):
    """
    An exception while unloading data from a DataSet.
    
    used by :mod:`fixture.loadable` classes
    """
    pass

class StorageMediaNotFound(LookupError):
    """
    Looking up a storable object failed.
    
    used by :mod:`fixture.loadable` classes
    """
    pass