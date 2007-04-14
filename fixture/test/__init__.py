
"""the fixture test suite.

The easiest way to run this is cd into the root and type:
$ python setup.py nosetests

You will need nose_ installed

Environment Variables
---------------------

The test suite is affected by several environment variables:

- FIXTURE_TEST_HEAVY_DSN
  
  - a database connection that can support operations like foreign key relations 
    (sqlite won't through foreign key errors)
  - defaults to None.
  - typically this would be a postgres connection where temp tables can be 
    created and destroyed
  - a special DSN, "sqlite:///:tmp:", will create a connection to a temporary 
    file-based sqlite db.  This is necessary because :memory: dbs can't be 
    shared easily using sqlalchemy (connections are not pooled)

- FIXTURE_TEST_LITE_DSN
  
  - a database as lite as possible, for speed
  - defaults to sqlite:///:memory:


.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

"""

import unittest, nose, os
from fixture.test import conf

def setup():
    # super hack:
    if conf.HEAVY_DSN == 'sqlite:///:tmp:':
        conf.HEAVY_DSN_IS_TEMPIO = True
        conf.reset_heavy_dsn()
    
    # this is here because the doc generator also runs doctests.
    # should fix that to use proper _test() methods for a module
    teardown_examples()

def teardown():
    teardown_examples()

def teardown_examples():
    if os.path.exists('/tmp/fixture_example.db'):
        os.unlink('/tmp/fixture_example.db')
        

class PrudentTestResult(unittest.TestResult):
    """A test result that raises an exception immediately"""
    def _raise_err(self, err):
        exctype, value, tb = err
        raise Exception("%s: %s" % (exctype, value)), None, tb
        
    def addFailure(self, test, err):
        self._raise_err(err)
    def addError(self, test, err):
        self._raise_err(err)
            
def attr(**kwargs):
    """Add attributes to a test function/method/class"""
    def wrap(func):
        func.__dict__.update(kwargs)
        return func
    return wrap
    

        