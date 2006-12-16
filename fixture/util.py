
"""fixture utilties."""

class ObjRegistry:
    """registers objects by class."""
    def __init__(self):
        self.registry = {}
    
    def has(self, object):
        return self.id(object) in self.registry
    
    def id(self, object):
        return id(object.__class__)
    
    def register(self, object):
        self.registry[self.id(object)] = 1
        
        