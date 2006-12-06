
"""
module for installing and reading test data

fixture provides an interface for loading tabular data into
various storage media such as a database, CSV file, XML file, et
cetera. This is useful for testing and aims to solve this
common problem:

    You have a test that wants to work with lots of data and you
    need a way to easily reference that data when making assertions.

Note that this module is a rewrite of the fixtures interface
first distributed in http://testtools.python-hosting.com/

INSTALL
-------

from the root source directory:

    python setup.py install

or if you have the easy_install command:
    
    easy_install fixture

SOURCE
------

http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev

"""

__version__ = "1.0"

# probably change this ...
#from fixture.loader import Loader as _defaultloader
_defaultloader = None

from fixture.exc import UninitializedError


def getdefault(key):
    def _getdefault(self):
        if len(self.values[key]) == 0:
            raise UninitializedError("your default %s has not been set" % key)
        return self.values[key][-1]
    return _getdefault

def setdefault(key):
    def _setdefault(self, newval):
        if newval is None:
            if len(self.values[key]) <= 1:
                # can't overwrite default
                return
            self.values[key].pop()
        else:
            self.values[key].append(newval)
    return _setdefault

class DefaultContainer(object):
    values = {
        'loader': [] # default val here
    }
    loader = property(getdefault('loader'), setdefault('loader'))
defaults = DefaultContainer()

    
from components import *
from dataset import DataSet