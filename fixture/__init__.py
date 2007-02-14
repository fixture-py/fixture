
"""
python module for loading and referencing test data

fixture provides an interface for loading tabular data into storage media. You create generic !DataSet objects that can be loaded into a database, CSV file, or anything else suitable.  This is useful for testing and came about to solve problems like these:

  * Your test needs to load lots of data and you want to easily reference that data when making assertions.
  * You want to group together commonly loaded data for your tests and keep this separate from assertions.
  * You want data linked by foreign key to load automatically and delete without integrity error.
  * You want to reference linked rows by variable name, not hard-coded ID number.
  * In fact, you don't even want to worry about auto-incrementing sequences and you don't want to repeat column values that don't change.
  * You want to recreate an environment (say, for a bug) by using fixture code generated from a database query (see `fixture.command.generate`).


!DataSet objects are written as python classes, without the need to type auto-incrementing IDs; referencing other data sets is simple::
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
    
}}}

Note that this module is more or less a complete rewrite of the fixtures interface first distributed in [http://testtools.python-hosting.com/ testtools].  The new interface still has room to evolve and there are probably a couple undiscovered bugs so please don't hesitate to [http://code.google.com/p/fixture/issues/list submit an issue].

===Source===

[http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev browse] the source online or [http://code.google.com/p/fixture/source follow these instructions] to checkout the code. 

===Install===

from the root source directory:

{{{
python setup.py install
}}}

or if you have the [http://peak.telecommunity.com/DevCenter/EasyInstall easy_install] command:

{{{
easy_install fixture
}}}

"""

__version__ = "1.0"

from fixture.loadable import *
from fixture.dataset import *
from fixture.util import *
from fixture.io import *


def setup_test_not_supported():
    """hook for setup for the test command."""
    raise NotImplementedError("use: `python setup.py nosetests` instead")
    