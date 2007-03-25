
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

- FIXTURE_TEST_LITE_DSN
  
  - a database as lite as possible, for speed
  - defaults to sqlite:///:memory:


.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

"""

import unittest
import nose

class PrudentTestResult(unittest.TestResult):
    """A test result that raises an exception immediately"""
    def _raise_err(self, err):
        exctype, value, tb = err
        raise Exception("%s: %s" % (exctype, value)), None, tb
        
    def addFailure(self, test, err):
        self._raise_err(err)
    def addError(self, test, err):
        self._raise_err(err)