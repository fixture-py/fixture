
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

class Fixture(object):
    """defines an environment for loading data.
    
    An instance of this class can safely be a module-level object.
    
    Keywords
    --------
    - dataclass
      
      - class to instantiate for datasets.  Default is fixture.dataset.SuperSet
    
    - loader
      
      - callable to instantiate and load data sets with.
      
    """
    dataclass = SuperSet
    loader = None
    
    class Data(object):
        """loads one or more data sets and provides an interface to that data.    
        """
        def __init__(self, datasets, dataclass, loader):
            self.datasets = datasets
            self.dataclass = dataclass
            self.loader = loader
            self.data = None # instance of dataclass
    
        def __enter__(self):
            self.setup()
    
        def __exit__(self):
            self.teardown()
    
        def __getattr__(self, name):
            """self.name is self.data.name"""
            return getattr(self.data, name)
    
        def __getitem__(self, name):
            """self['name'] is self.data['name']"""
            return self.data[name]
    
        def setup(self):
            self.data = self.dataclass(*[d() for d in self.datasets])
            self.loader.load(self.data)
    
        def teardown(self):
            self.loader.unload()
                
    def __init__(self, **attr):
        for k,v in attr.items():
            setattr(self, k, v)
    
    def __iter__(self):
        for k in self.__dict__:
            yield k
    
    def with_data(self, *datasets, **cfg):
        """returns a decorator to wrap data around a method.
    
        the method will receive a new first argument, the Fixture.Data instance.
    
        Keywords
        --------
        - setup
    
          - optional callable to be executed before test
     
        - teardown
        
          - optional callable to be executed (finally) after test

        """

        setup = cfg.get('setup', None)
        teardown = cfg.get('teardown', None)

        def decorate_with_data(routine):
            def setup_data():
                data = self.Data(datasets, self.dataclass, self.loader)
                data.setup()
                return data
            def teardown_data(data):
                data.teardown()
                if teardown: teardown()
        
            @wraps(routine)
            def call_routine(*a,**kw):
                data = setup_data()
                try:
                    routine(data, *a, **kw)
                finally:
                    teardown_data(data)
    
            @wraps(routine)
            def iter_routine():
                for stack in routine():
                    fn = stack[0]
                    try:
                        args = stack[1:]
                    except IndexError:
                        args = tuple([])
                    def atomic_routine(*genargs,**kw):
                        setup_data = genargs[0]
                        data = setup_data()
                        try:
                            genargs = genargs[1:]
                        except IndexError:
                            genargs = tuple([])
                        genargs = (data,) + genargs
                        try:
                            fn(*genargs, **kw)
                        finally:
                            teardown_data(data)
                    
                    restack = (atomic_routine, setup_data) + args
                    yield restack
            
            if is_generator(routine):
                wrapped_routine = iter_routine
            else:
                wrapped_routine = call_routine
        
            return with_setup( setup=setup )( wrapped_routine )
        return decorate_with_data
    
    def data(self, *datasets):
        """returns a Data object for datasets."""
        return self.Data(datasets, self.dataclass, self.loader)
        