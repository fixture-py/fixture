
"""the fixture test suite.

The easiest way to run this is cd into the root and type:
$ python setup.py nosetests

You will need nose_ installed

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