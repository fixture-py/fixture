
"""fixture utilties."""

import sys
import unittest
import types
import logging

__all__ = ['DataTestCase']

class DataTestCase(object):
    """A mixin to use with unittest.TestCase.
    
    Say you have a storage medium (in this case, sqlalchemy) defined like so::
        
        >>> from sqlalchemy import *
        >>> meta = BoundMetaData("sqlite:///:memory:")
        >>> session = create_session(bind_to=meta.engine)
        >>> events = Table('events', meta, 
        ...     Column('id', INT, primary_key=True),
        ...     Column('name', String))
        >>> meta.create_all()
    
    And a DataSet to load::
    
        >>> from fixture import DataSet
        >>> class events_data(DataSet):
        ...     class click:
        ...         id=1
        ...         name="click"
        ...
    
    You can create a concrete test case class like this::
    
        >>> from fixture import DataTestCase, SQLAlchemyFixture
        >>> from fixture.style import TrimmedNameStyle
        >>> class TestWithEvents(DataTestCase, unittest.TestCase):
        ...     fixture = SQLAlchemyFixture(
        ...                     env=globals(), session=session,
        ...                     style=TrimmedNameStyle(suffix="_data"))
        ...     datasets = [events_data]
        ...
        ...     def testSomething(self):
        ...         assert self.data.events_data.click.name == "click"
        ...
    
    Behind the scenes, unittest will run it for you as usual...
    
        >>> import unittest
        >>> res = unittest.TestResult()
        >>> loader = unittest.TestLoader()
        >>> suite = loader.loadTestsFromTestCase(TestWithEvents)
        >>> r = suite(res)
        >>> res.failures
        []
        >>> res.errors
        []
        >>> res.testsRun
        1
    
    """
    fixture = None
    data = None
    datasets = []
    def setUp(self):
        if self.fixture is None:
            raise NotImplementedError("no concrete fixture to load data with")
        if not self.datasets:
            raise ValueError("there are no datasets to load")
        self.data = self.fixture.data(*self.datasets)
        self.data.setup()
    
    def tearDown(self):
        self.data.teardown()

class ObjRegistry:
    """registers objects by class.
    
    all lookup methods expect to get either an instance or a class type.
    """
    def __init__(self):
        self.registry = {}
    
    def __repr__(self):
        return repr(self.registry)
    
    def __getitem__(self, obj):
        try:
            return self.registry[self.id(obj)]
        except KeyError:
            etype, val, tb = sys.exc_info()
            raise KeyError("object %s is not in registry" % obj), None, tb
    
    def __contains__(self, object):
        return self.has(object)
    
    def clear(self):
        self.registry = {}
    
    def has(self, object):
        return self.id(object) in self.registry
    
    def id(self, object):
        if hasattr(object, '__class__'):
            if issubclass(object.__class__, type):
                # then it's a class...
                cls = object
            else:
                # instance ...
                cls = object.__class__
        elif type(object)==types.ClassType:
            # then it's a classic class (no metaclass)...
            cls = object
        else:
            raise ValueError(
                    "cannot identify object %s because it isn't an "
                    "instance or a class" % object)
        return id(cls)
    
    def register(self, object):
        id = self.id(object)
        self.registry[id] = object
        return id

def with_debug(*channels, **kw):
    """A nose decorator calls start_debug/start_debug before and after the 
    decorated method.
    
    All positional arguments are considered channels that should be debugged.  
    Keyword arguments are passed to start_debug()
    """
    from nose.tools import with_setup
    def setup():
        for ch in channels:
            start_debug(ch, **kw)
    def teardown():
        for ch in channels:
            stop_debug(ch)
    return with_setup(setup=setup, teardown=teardown)

def start_debug(channel, stream=sys.stdout, handler=None):
    """A shortcut to start logging a channel to a stream.
    
    For example::
    
        >>> from fixture.util import start_debug, stop_debug
        >>> start_debug("fixture.loadable")
    
    starts logging messages from the fixture.loadable channel to the stream.  
    Then... ::
    
        >>> stop_debug("fixture.loadable")
    
    ...turns it off.
    
    Available Channels
    ------------------
    - fixture.loadable
    
      - logs LOAD and CLEAR messages, referring to dataset actions
    
    - fixture.loadable.tree
    
      - logs a tree view of datasets loaded by datasets (recursion)
    
    .. _api::
        
        Keyword Arguments
        -----------------
        - stream
        
          - stream to create a loggin.StreamHandler with.  defaults to stdout
        
        - handler
        
          - a preconfigured handler to add to the log
    
    """
    log = logging.getLogger(channel)
    stop_debug(channel)
    if not handler:
        handler = logging.StreamHandler(stream)
    log.addHandler(handler)

def stop_debug(channel):
    """The reverse of start_debug()."""
    log = logging.getLogger(channel)
    # reset all handlers (are you going to kill me?)
    for h in log.handlers:
        if not issubclass(h.stream.__class__, _dummy_stream):
            log.removeHandler(h)

class _dummy_stream(object):
    def write(self, *a,**kw): pass
    def flush(self, *a, **kw): pass

def _mklog(channel, default_level=logging.INFO, default_stream=None):
    """returns a log object that does nothing until something adds a 
    useful handler to it
    """
    log = logging.getLogger(channel)
    log.setLevel(default_level)
    if not default_stream:
        default_stream = logging.StreamHandler(_dummy_stream())
    log.addHandler(default_stream)
    return log
        