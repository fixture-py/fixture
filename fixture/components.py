
"""fixture components."""

from fixture.dataset import SuperSet

class affix(object):
    """loads all datasets atomically.
    
    Keywords
    --------
    - superset
      
      - Style of fixture.dataset to return.  Default is
        fixture.dataset.SuperSet
    
    - loader
      
      - Style of fixture.loader to load data sets with.
        NOTE: If *any* dataset specifies its own loader, that will 
        take precedence.  In absence of this value, 
        fixture.loader.default will be used.
    
    """
    def __init__(self, *datasets, **kw):
        self.superset = kw.get('superset', SuperSet)
    
    def __enter__(self):
        self.setup()
    
    def __exit__(self):
        self.teardown()
    
    def __getattribute__(self, name):
        """self.name is always self.superset.name."""
        return self.superset.__getattribute__(name)
    
    def setup(self):
        # use loader(s) to load all data sets
        pass
    
    def teardown(self):
        # use loader(s) to tear down all data sets
        pass
    