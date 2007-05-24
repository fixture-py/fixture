
"""
python module for loading and referencing test data

fixture provides several utilities for achieving a _fixed state_ when testing 
python programs.  Specifically, these setup/teardown databases and/or work with 
a temporary file system.  This is useful for testing and came about to solve 
problems like these:

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

"Database testing is easier than I had thought. Kumar's fixture helps provide a stable database to drive testing." -- [http://homepage.mac.com/s_lott/iblog/architecture/C1597055042/E20070226153515/index.html Steven F. Lott]

===Documentation===

 * [http://farmdev.com/projects/fixture/docs/ End User Documentation]
 * [http://farmdev.com/projects/fixture/apidocs/ API Documentation]

===Install===

Using the [http://peak.telecommunity.com/DevCenter/EasyInstall easy_install] command:

{{{easy_install fixture}}}

Or, if you want to create a link to the source without installing anything, cd into the root directory and type:

{{{python setup.py develop}}}

Or ... if you're old school, this works with or without [http://peak.telecommunity.com/DevCenter/setuptools setuptools]:

{{{python setup.py install}}}

===Requirements===

At the moment fixture is only tested on Python 2.4 and 2.5 so it may or may not 
work with earlier versions.  If you submit a patch to support an earlier 
version, I will try my best to accommodate it.

The module does not depend on external libraries for its core functionality but 
to so something interesting you will need one of several libraries, detailed in 
the documentation.  You can also run the test suite if to see what was skipped 
due to dependency error.

===Source===

[http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev browse] the source online or [http://code.google.com/p/fixture/source follow these instructions] to checkout the code. 

===Status===

fixture is more or less a complete rewrite of 
[http://testtools.python-hosting.com/ testtools.fixtures].  Since testtools went 
through several versions, fixture claims to be a 1.0 release.  All 
that means is that the implementation is now thought to be more mature and at 
any final release, a major effort will be made to preserve the interface through 
regression testing.

However, the new interface still has room to evolve and there are probably 
undiscovered bugs so please don't hesitate to 
[http://code.google.com/p/fixture/issues/list submit an issue].

"""

__version__ = "1.0"

import logging
import sys

from fixture.loadable import *
from fixture.dataset import *
from fixture.util import *
from fixture.io import *

def setup_test_not_supported():
    """hook for setup for the test command."""
    raise NotImplementedError("use: `python setup.py nosetests` instead")
    