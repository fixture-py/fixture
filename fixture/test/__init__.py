
"""The fixture test suite.


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
 
As a shortcut, you can run this to set these variables in your shell ::
    
    $ source fixture/test/profile/full.sh

"""

import os
import unittest

from six import reraise

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
    if os.path.exists('/tmp/fixture_generate.db'):
        os.unlink('/tmp/fixture_generate.db')
        

class PrudentTestResult(unittest.TestResult):
    """A test result that raises an exception immediately"""
    def _raise_err(self, err):
        exctype, value, tb = err
        reraise(Exception, Exception("%s: %s" % (exctype, value)), tb)

    def addFailure(self, test, err):
        self._raise_err(err)
    def addError(self, test, err):
        self._raise_err(err)

class _SilentTestResult(PrudentTestResult):
    def printErrors(self):
        pass
    def printErrorList(self, flavour, errors):
        pass
        
class SilentTestRunner(unittest.TextTestRunner):
    """a test runner that doesn't print output but raises 
    exceptions immediately
    """
    def _makeResult(self): 
        return _SilentTestResult()
        
    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        test(result)
        return result
            
def attr(**kwargs):
    """Add attributes to a test function/method/class"""
    def wrap(func):
        func.__dict__.update(kwargs)
        return func
    return wrap
    

        