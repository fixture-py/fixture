
from fixture.exc import UninitializedError
default = None

class LazyLoader(object):
    def __init__(self, loader=default):
        self.loader = loader
    def __call__(self):
        if self.loader is None:
            raise UninitializedError("no default loader has been set")
        return self.loader()