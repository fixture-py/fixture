
"""base Fixture components.

The more useful bits are in LoadableFixture

"""

try:
    from functools import wraps
except ImportError:
    # for python < 2.5... this is a limited set of what we need to do
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
    """An environment for loading data.
    
    An instance of this class can safely be a module-level object.
    It may be more useful to use a concrete LoadableFixture, such as
    SQLAlchemyFixture
    
    Keywords
    --------
    - dataclass
  
      - class to instantiate with datasets (defaults to SuperSet)

    - loader
  
      - class to instantiate and load data sets with.
      
    """
    dataclass = SuperSet
    loader = None
    
    class Data(object):
        """loads one or more DataSet objects and provides an interface into that data.    
        """
        def __init__(self, datasets, dataclass, loader):
            self.datasets = datasets
            self.dataclass = dataclass
            self.loader = loader
            self.data = None # instance of dataclass
    
        def __enter__(self):
            """enter a with statement block.
            
            calls self.setup()
            """
            self.setup()
            return self
    
        def __exit__(self, type, value, traceback):
            """exit a with statement block.
            
            calls self.teardown()
            """
            self.teardown()
    
        def __getattr__(self, name):
            """self.name is self.data.name"""
            return getattr(self.data, name)
    
        def __getitem__(self, name):
            """self['name'] is self.data['name']"""
            return self.data[name]
    
        def setup(self):
            """load all datasets, populating self.data."""
            self.data = self.dataclass(*[
                        ds.shared_instance( default_refclass=self.dataclass ) \
                            for ds in iter(self.datasets)])
            self.loader.load(self.data)
    
        def teardown(self):
            """unload all datasets."""
            self.loader.unload()
                
    def __init__(self, dataclass=None, loader=None):
        if dataclass:
            self.dataclass = dataclass
        if loader:
            self.loader = loader
    
    def __iter__(self):
        for k in self.__dict__:
            yield k
    
    def with_data(self, *datasets, **cfg):
        """returns a decorator to wrap data around a method.
        
        All positional arguments are DataSet class objects.
        
        the decorated method will receive a new first argument, 
        the Fixture.Data instance.
    
        Keywords
        --------
        - setup
    
          - optional callable to be executed before test
     
        - teardown
        
          - optional callable to be executed (finally) after test

        """
        from nose.util import is_generator
        from nose.tools import with_setup

        setup = cfg.get('setup', None)
        teardown = cfg.get('teardown', None)

        def decorate_with_data(routine):
            # passthrough an already decorated routine:
            # (could this be any uglier?)
            if hasattr(routine, 'setup'):
                def passthru_setup():
                    routine.setup()
                    if setup: setup()
            else:
                passthru_setup = setup
            if hasattr(routine, 'teardown'):
                def passthru_teardown():
                    routine.teardown()
                    if teardown: teardown()
            else:
                passthru_teardown = teardown
            
            def setup_data():
                data = self.data(*datasets)
                data.setup()
                return data
            def teardown_data(data):
                data.teardown()
        
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
        
            decorate = with_setup(  setup=passthru_setup, 
                                    teardown=passthru_teardown )
            return decorate( wrapped_routine )
        return decorate_with_data
    
    def data(self, *datasets):
        """returns a Data object for datasets."""
        return self.Data(datasets, self.dataclass, self.loader)
        