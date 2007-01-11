
"""fixture utilties."""

class ObjRegistry:
    """registers objects by class."""
    def __init__(self):
        self.registry = {}
    
    def __contains__(self, object):
        return self.has(object)
    
    def has(self, object):
        return self.id(object) in self.registry
    
    def id(self, object):
        return id(object.__class__)
    
    def register(self, object):
        id = self.id(object)
        self.registry[id] = object
        return id
        
        