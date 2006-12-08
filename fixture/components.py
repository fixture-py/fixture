
"""fixture components."""

from nose.util import is_generator
from nose.tools import with_setup
try:
    from functools import wraps
except ImportError:
    # this is a limited set of what we need to do
    # with a wrapped function :
    def wraps(f):
        def wrap_with_f(new_f):
            new_f.__name__ = f.__name__
            if hasattr(f, '__module__'):
                new_f.__module__ = f.__module__
            return new_f
        return wrap_with_f
        
from fixture.dataset import SuperSet
from fixture import defaults

class fixtures(object):
    """loads data sets atomically.
    
    Keywords
    --------
    - setclass
      
      - Class to store data sets in.  Default is fixture.dataset.SuperSet
    
    - loader
      
      - fixture.loader class to instantiate and load data sets with.  
        Defaults to fixture.defaults.loader
    
    """
    def __init__(self, *datasets, **kw):
        self.datasets = datasets
        self.get_loader =  kw.get('loader', defaults.loader)
        self.loader = None
        self.setclass = kw.get('metaset', SuperSet)
        self.superset = None
    
    def __enter__(self):
        self.setup()
    
    def __exit__(self):
        self.teardown()
    
    def __getattr__(self, name):
        """self.name is self.superset.name."""
        return getattr(self.superset, name)
    
    def setup(self):
        self.superset = self.setclass(*self.datasets)
        self.loader = self.get_loader()
        self.loader.setup(self.superset)
        return self.superset
    
    def teardown(self):
        if self.loader.is_loaded:
            self.loader.teardown(self.superset)

def with_fixtures(*datasets, **cfg):
    """decorates method with loaded fixtures.
    
    first argument to decorated method will be a fixtures() instance.
    
    Keyword Args:
    -------------
    - setup -- a callable to be executed before test
    - teardown -- a callable to be executed (finally) after test
    - loader -- a loader object to use
    
    For example :
    
    >>> from fixture import DataSet
    >>> class MyBooks(DataSet):
    ...     lolita = dict(title='lolita')
    ...     pi = dict(title='life of pi')
    ... 
    >>> @with_fixtures(MyBooks)
    ... def test_with_books(fxt):
    ...     print fxt.lolita
    ...     # test something ...
    ... 
    >>> test_with_books()
    <DataRow {'title': 'lolita'}>
    >>> 
    
    """
    
    setup = cfg.get('setup', None)
    teardown = cfg.get('teardown', None)
    loader = cfg.get('loader', defaults.loader)
    
    def with_fixtures_deco(passthru):
        def setup_fxt():
            fxt = fixtures(*datasets)
            fxt.setup()
            return fxt
        def teardown_fxt(fxt):
            fxt.teardown()
            if teardown: teardown()
            
        @wraps(passthru)
        def passthru_by_call(*a,**kw):
            fxt = setup_fxt()
            try:
                passthru(fxt, *a, **kw)
            finally:
                teardown_fxt(fxt)
        
        @wraps(passthru)
        def passthru_by_iter():
            # wow, this could use a rewrite
            for stack in passthru():
                fn = stack[0]
                # might fail if no args...
                args = stack[1:]
                
                def atomic_passthru(*genargs,**kw):
                    setup_fxt = genargs[0]
                    fxt = setup_fxt()
                    # might fail again if no args...
                    genargs = (fxt,) + genargs[1:]
                    try:
                        fn(*genargs, **kw)
                    finally:
                        teardown_fxt(fxt)
                        
                restack = (atomic_passthru, setup_fxt) + args
                yield restack
                
        if is_generator(passthru):
            passthru_by_call = passthru_by_iter
            
        return with_setup( setup=setup )( passthru_by_call )
    return with_fixtures_deco