
from fixture.exc import UninitializedError
default = None

class LazyLoader(object):
    def __init__(self, **kw):
        if kw.has_key('loader'):
            loader = kw['loader']
            del kw['loader']
        else:
            loader = default
        self.kw = kw
        self.loader = loader
        
    def __call__(self, **kw):
        self.kw.update(kw)
        if self.loader is None:
            raise UninitializedError("fixture.loader.default has not been set")
        return self.loader(**self.kw)