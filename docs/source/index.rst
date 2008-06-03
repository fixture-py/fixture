
========================
Using the fixture module
========================

fixture is a python module for loading and referencing test data

It provides several utilities for achieving a *fixed state* when testing 
Python programs.  Specifically, these utilities setup / teardown databases and 
work with temporary file systems.  This is useful for testing and came about to 
fulfill stories like these:

- Your test needs to load data into a database and you want to easily reference that data when making assertions.
- You want data linked by foreign key to load automatically and delete without integrity error.
- You want to reference linked rows by meaningful names, not hard-coded ID numbers.
- You don't want to worry about auto-incrementing sequences.
- You want to recreate an environment (say, for a bug) by querying a database for real data (see the `fixture` command).
- You want to work easily with files in a temporary, transparent file system.

For more info, this concept is explained in the wikipedia article, `Test Fixture`_.

.. _Test Fixture: http://en.wikipedia.org/wiki/Test_fixture

------------------
Download / Install
------------------

Using the easy_install_ command::

    easy_install fixture

The source is available from the `fixture package`_ or the `fixture subversion repository`_ and this works with or without setuptools_::

    cd /path/to/source
    python setup.py install
    

.. note::
    The above commands may require root access

.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _fixture package: http://pypi.python.org/pypi/fixture
.. _fixture subversion repository: http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev

---------------------------------
Loading and referencing test data
---------------------------------

There are a couple ways to test a database-backed application.  You can create `mock objects`_ and concentrate entirely on `unit testing`_ individual components without testing the database layer itself, or you can simply load up sample data before you run a test.  Thanks to ``sqlite`` in-memory connections (a special DSN, ``sqlite:///:memory:``), the latter may be more efficient than you think.  

But it's easy enough to insert data line by line in code, right?  Or simply load a SQL file?  Yes, but this has two major downsides: you often have to worry about and manage complex chains of foreign keys manually; and when referencing data values later on, you either have to copy/paste the values or pass around lots of variables.

The fixture module simplifies this by breaking the process down to two independent components:

**DataSet**
    Defines sets of sample data
**Fixture**
    Knows how to load data

.. _mock objects: http://en.wikipedia.org/wiki/Mock_object
.. _unit testing: http://en.wikipedia.org/wiki/Unit_testing
.. _functional test: http://en.wikipedia.org/wiki/Functional_test
.. _code coverage: http://en.wikipedia.org/wiki/Code_coverage


Now, on to the knitty gritty details ...

.. toctree::
   :maxdepth: 2
   
   using-dataset
   using-loadable-fixture
   using-fixture-cmd
   using-temp-io
   
-----------------
API Documentation
-----------------

`See API documentation`_ for detailed documentation of individual ``fixture`` components

.. _See API documentation: ../apidocs/index.html

-------------------------------------
Where to submit issues, patches, bugs
-------------------------------------

Please submit any issues, patches, failing tests, and/or bugs using the `Issue
Tracker`_ on the `fixture project site`_. Even vague ideas for improvement are welcome. If your code is used, your contribution will be
documented.

.. _Issue Tracker: http://code.google.com/p/fixture/issues/list
.. _fixture project site: http://code.google.com/p/fixture/
