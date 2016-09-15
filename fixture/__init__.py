
"""fixture is a python module for loading and referencing test data

It provides several utilities for achieving a *fixed state* when testing
Python programs.  Specifically, these utilities setup / teardown databases and
work with temporary file systems.

You may want to start by reading the `End User Documentation`_.

.. _End User Documentation: http://farmdev.com/projects/fixture/docs/

If you are reading this from a `source checkout`_ then you may want to build the documentation locally.  Install `Sphinx`_ then run::

    cd /path/to/fixture/source
    cd docs
    make html

Then open ``build/html/index.html`` in your web browser.  If that fails, you can read the reST files starting at ``docs/source/index.rst``

.. _source checkout: http://fixture.googlecode.com/hg/#egg=fixture-dev
.. _Sphinx: http://sphinx.pocoo.org/

"""

from pkg_resources import get_distribution

__version__ = get_distribution("fixture").version

import logging
import sys

from fixture.dataset import *
from fixture.io import *
from fixture.loadable import *
from fixture.style import *
from fixture.util import *


def setup_test_not_supported():
    """hook for setup for the test command."""
    raise NotImplementedError("use: `python setup.py nosetests` instead")
setup_test_not_supported.__test__ = False

