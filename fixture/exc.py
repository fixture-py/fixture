
"""Fixture exceptions"""

class UninitializedError(Exception):
    pass

class DataSetActionException(Exception):
    """an exception while performing some action with a DataSet."""
    def __init__(self, etype, val, dataset, 
                        key=None, row=None, stored_object=None):
        msg = "in %s" % dataset
        if key or row:
            msg = "with '%s' of '%s' %s" % (key, row, msg)
        elif stored_object:
            msg = "with %s %s" % (stored_object, msg)
        
        Exception.__init__(self, "%s: %s (%s)" % (etype.__name__, val, msg))
        
class LoadError(DataSetActionException):
    """an exception while loading data in DataSet."""
    pass
class UnloadError(DataSetActionException):
    """an exception while unloading data from a DataSet."""
    pass

class StorageMediaNotFound(LookupError):
    """Looking up a storable object failed.
    
    used by :mod:`fixture.loadable` classes
    """
    pass