
"""
python module for loading and referencing test data

fixture provides an interface for loading tabular data into arbitrary storage media. You create generic fixture.!DataSet objects that can be loaded into a database, CSV file, XML file, or anything else suitable.  This is useful for testing and came about to solve problems like these:

  * Your test needs to load lots of data and you want to easily reference that data when making assertions.
  * You want to group together commonly loaded data for your tests and keep this separate from the assertions.
  * You want data linked by foreign key to load automatically and delete without integrity errors.
  * You want to reference linked rows by variable name, not hard-coded ID number.
  * In fact, you don't even want to worry about auto-incrementing sequences and you don't want to repeat column values that don't change.
  * You want to recreate an environment (say, for a bug) by using fixture code generated from a database query (fixture.command.generate).

Note that this module is more or less a complete rewrite of the fixtures interface 
first distributed in [http://testtools.python-hosting.com/ testtools].  The new interface still has room to evolve and there are probably a couple undiscovered bugs so please don't hesitate to [http://code.google.com/p/fixture/issues/list submit an issue].

===Install===

from the root source directory:

{{{
python setup.py install
}}}

or if you have the [http://peak.telecommunity.com/DevCenter/EasyInstall easy_install] command:

{{{
easy_install fixture
}}}

===Source===

[http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev browse] the source online or [http://code.google.com/p/fixture/source follow these instructions] to checkout the code. 

"""

__version__ = "1.0"
    
from components import Fixture
from dataset import DataSet