
"""fixture utilities"""

from fixture.exc import UninitializedError

def getdefault(key):
    def _getdefault(self):
        try:
            return self.values[key][-1]
        except IndexError:
            raise UninitializedError(
                "your default %s has not been set" % key)
    return _getdefault

def setdefault(key):
    def _setdefault(self, newval):            
        if newval is None:
            if len(self.values[key]) <= 1:
                # can't overwrite default
                return
            self.values[key].pop()
        else:
            self.values[key].append(newval)
    return _setdefault

class DefaultContainer(object):
    
    values = {
        'loader': [] # default val
    }        
    loader = property(getdefault('loader'), setdefault('loader'))
    
    def __init__(self):
        self.tmp_vars = None
    
    def __call__(self, **tmp_vars):
        """sets temporary defaults during a with-statement block.
        """
        self.tmp_vars = tmp_vars
    
    def __enter__(self):
        if not self.tmp_vars:
            raise UninitializedError(
                    "can't enter block without temp vars to set")
        for k,v in self.tmp_vars.items():
            # dict update will still trigger properties?
            setattr(self, k, v)
    
    def __exit__(self):
        for k,v in self.tmp_vars.items():
            setattr(self, k, None)