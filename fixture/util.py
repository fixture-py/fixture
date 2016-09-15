
"""Fixture utilties."""

import sys
import types
import logging

from six import reraise


__all__ = ['DataTestCase']

class DataTestCase(object):
    """
    A mixin to use with unittest.TestCase.
    
    Upon setUp() the TestCase will load the DataSet classes using your Fixture, 
    specified in class variables.  At tearDown(), all loaded data will be 
    removed.  During your test, you will have ``self.data``, a SuperSet instance 
    to reference loaded data
    
    Class Attributes:
    
    ``fixture``
        the :class:`Fixture <fixture.base.Fixture>` instance to load :class:`DataSet <fixture.dataset.DataSet>` classes with
    
    ``datasets``
        A list of :class:`DataSet <fixture.dataset.DataSet>` classes to load
    
    ``data``
        ``self.data``, a :class:`Fixture.Data <fixture.base.FixtureData>` instance populated for you after ``setUp()``
    
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
            reraise(KeyError, KeyError("object %s is not in registry" % obj))
    
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
    """
    A `nose`_ decorator calls :func:`start_debug` / :func:`start_debug` before and after the 
    decorated method.
    
    All positional arguments are considered channels that should be debugged.  
    Keyword arguments are passed to :func:`start_debug`
    
    .. _nose: http://somethingaboutorange.com/mrl/projects/nose/
    
    """
    from nose.tools import with_setup
    def setup():
        for ch in channels:
            start_debug(ch, **kw)
    def teardown():
        for ch in channels:
            stop_debug(ch)
    return with_setup(setup=setup, teardown=teardown)

def reset_log_level(level=logging.CRITICAL, channels=(
                                            "fixture.loadable",
                                            "fixture.loadable.tree")):
    """
    Resets the level on all fixture logs.
    
    You may need to call this when other applications 
    reset the root logger's log level.
    
    Calling this with no args sets all logs to logging.CRITICAL
    which should keep them quiet
    
    Added in version 1.1
    """
    for ch in channels:
        logging.getLogger(ch).setLevel(level)

def start_debug(channel, stream=sys.stdout, handler=None, level=logging.DEBUG):
    """
    A shortcut to start logging a channel to a stream.
    
    For example::
    
        >>> from fixture.util import start_debug, stop_debug
        >>> start_debug("fixture.loadable")
    
    starts logging messages from the fixture.loadable channel to the stream.  
    Then... ::
    
        >>> stop_debug("fixture.loadable")
    
    ...turns it off.
    
    Available Channels:
    
    ``fixture.loadable``
        logs LOAD and CLEAR messages, referring to dataset actions
    
    ``fixture.loadable.tree``
        logs a tree view of datasets loaded by datasets (recursion)
    
        
    Keyword Arguments:
    
    ``stream``
        stream to create a loggin.StreamHandler with.  defaults to stdout.
    
    ``handler``
        a preconfigured handler to add to the log
    
    ``level``
        a logging level to set, default is logging.DEBUG
    
    
    .. note:: 
        Other applications might add a handler to the root logger, 
        in which case you can't turn off debug output without messing 
        with the root logger.
    
    
    """
    log = logging.getLogger(channel)
    if not handler:
        handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    for h in log.handlers:
        log.removeHandler(h)
    log.addHandler(handler)
    log.setLevel(level)

def stop_debug(channel=None):
    """The reverse of :func:`start_debug`."""
    reset_log_level(channels=[channel])

class _dummy_stream(object):
    def write(self, *a,**kw): pass
    def flush(self, *a, **kw): pass

def _mklog(channel, default_level=logging.CRITICAL, default_stream=None):
    """
    returns a log object that does nothing until something 
    calls start_debug()
    """
    log = logging.getLogger(channel)
    log.setLevel(default_level)
    if not default_stream:
        default_stream = logging.StreamHandler(_dummy_stream())
    log.addHandler(default_stream)
    return log

try:
    any = any
except NameError:
    # 2.4-
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

        