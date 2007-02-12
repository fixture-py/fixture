
"""fixture utilties."""

import sys
import unittest
import types

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
        
        