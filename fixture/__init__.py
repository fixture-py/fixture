
"""
python module for loading and referencing test data

fixture provides several utilities for achieving a _fixed state_ when testing 
python programs.  Specifically, these are designed to setup/teardown database 
data and/or work with a temporary file system.  This is useful for testing and 
came about to solve problems like these:

  * Your test needs to load data into a database and you want to easily reference that data when making assertions.
  * You want data linked by foreign key to load automatically and delete without integrity error.
  * You want to reference linked rows by variable name, not hard-coded ID number.
  * In fact, you don't even want to worry about auto-incrementing sequences and you don't want to repeat column values that don't change.
  * You want to recreate an environment (say, for a bug) by using real data generated from a database query (see `fixture.command.generate`).
  * You want to work with files in a temporary file system.

For more info, this concept is explained in the wikipedia article, [http://en.wikipedia.org/wiki/Test_fixture Test Fixture].

===DataSet Objects===

To load data into a database (or anything suitable) you create subclasses of 
`fixture.DataSet` like so:

{{{

    >>> class BannerData(DataSet):
    ...     class free_spaceship:
    ...         text="Get a free spaceship with any purchase"
    ...
    >>> class EventData(DataSet):
    ...     class click:
    ...         name="click"
    ...         banner_id=BannerData.free_spaceship.ref('id')
    ...     class submit(click):
    ...         name="submit"
    ...     class order(click):
    ...         name="order"
    ...
    >>> 
}}}

===Source===

[http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev browse] the source online or [http://code.google.com/p/fixture/source follow these instructions] to checkout the code. 

===Install===

Using the [http://peak.telecommunity.com/DevCenter/EasyInstall easy_install] command:

{{{easy_install fixture}}}

Or, if you want to create a link to the source without installing anything, cd into the root directory and type:

{{{python setup.py develop}}}

Or ... if you're old school, this works with or without [http://peak.telecommunity.com/DevCenter/setuptools setuptools]:

{{{python setup.py install}}}



Note that this module is more or less a complete rewrite of the fixtures interface first distributed in [http://testtools.python-hosting.com/ testtools].  The new interface still has room to evolve and there are probably a couple undiscovered bugs so please don't hesitate to [http://code.google.com/p/fixture/issues/list submit an issue].

"""

__version__ = "1.0"

from fixture.loadable import *
from fixture.dataset import *
from fixture.util import *
from fixture.io import *


def setup_test_not_supported():
    """hook for setup for the test command."""
    raise NotImplementedError("use: `python setup.py nosetests` instead")
    