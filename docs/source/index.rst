
========================
Using the fixture module
========================

fixture is a python module for loading and referencing test data

It provides several utilities for achieving a *fixed state* when testing 
Python programs.  Specifically, these utilities setup / teardown databases and 
work with temporary file systems.  This is useful for testing and came about to 
fulfill stories like these:

- I want to load data into a test database and easily reference that data when making assertions.
- I want data linked by foreign key to load automatically and delete without integrity error.
- I want to reference linked rows by meaningful names, not hard-coded ID numbers.
- I don't want to worry about auto-incrementing sequences.
- I want to recreate an environment (say, for a bug) by querying a database for real data.
- I want to test with files in a temporary, transparent file system.

For more info, this concept is explained in the wikipedia article, `Test Fixture`_.

.. _Test Fixture: http://en.wikipedia.org/wiki/Test_fixture

*Database testing is easier than I had thought. Kumar's fixture helps provide a stable database to drive testing.* -- `Steven F. Lott, summarizing PyCon 2007`_

.. _Steven F. Lott, summarizing PyCon 2007: http://homepage.mac.com/s_lott/iblog/architecture/C1597055042/E20070226153515/index.html

.. _download-fixture:

------------------
Download / Install
------------------

Using the easy_install_ command::

    easy_install fixture

If you want to use decorators like :meth:`@fixture.with_data() <fixture.base.Fixture.with_data>` you need `nose`_ installed, so run::
    
    easy_install 'fixture[decorators]'

For more variants on the ``easy_install`` command, such as installing database libraries, see :ref:`Using LoadableFixture <using-loadable-fixture>`.

The source is available from the `fixture package`_ or the `fixture subversion repository`_ and the following command works with or without setuptools_::

    cd /path/to/source
    python setup.py install

.. note::
    The above commands may require root access
    
If you want to try out fixture before installing it globally, you may be interested in `virtualenv`_.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _fixture package: http://pypi.python.org/pypi/fixture
.. _fixture subversion repository: http://fixture.googlecode.com/svn/trunk/#egg=fixture-dev

------------
Requirements
------------

At the moment fixture is only tested on Python 2.4 and 2.5 so it may or may not 
work with other versions.  The module does not depend on external libraries for its core functionality but 
to do something interesting you will need one of several 3rd party libraries 
(explained later in the documentation).

---------------------------------
Loading and referencing test data
---------------------------------

There are a couple ways to test a database-backed application.  You can create `mock objects`_ and concentrate entirely on `unit testing`_ individual components without testing the database layer itself, or you can simply load up sample data before you run a test.  Thanks to ``sqlite`` in-memory connections, the latter may be more efficient than you think.  

But it's easy enough to insert data line by line in code, right?  Or simply load a SQL file?  Yes, but this has two major downsides: you often have to worry about and manage complex chains of foreign keys manually; and when referencing data values later on, you either have to copy / paste the values or pass around lots of variables.

The fixture module simplifies this by breaking the process down to two independent components:

**DataSet**
    Defines sets of sample data
**Fixture**
    Knows how to load data

.. _mock objects: http://en.wikipedia.org/wiki/Mock_object
.. _unit testing: http://en.wikipedia.org/wiki/Unit_testing
.. _functional test: http://en.wikipedia.org/wiki/Functional_test
.. _code coverage: http://en.wikipedia.org/wiki/Code_coverage

-----------------
Examples of Usage
-----------------

Fixture can be used to load :class:`DataSet <fixture.dataset.DataSet>` objects into `SQLAlchemy`_ or `SQLObject`_ backends (:ref:`more on that <using-loadable-fixture>`).  For a complete end-to-end example see :ref:`Using Fixture To Test A Pylons + SQLAlchemy App <using-fixture-with-pylons>`.  This should help you understand how to fit ``fixture`` into a finished app.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _SQLObject: http://www.sqlobject.org/

Now, on to the knitty gritty details ...

.. toctree::
   :maxdepth: 2
   
   using-dataset
   using-loadable-fixture
   using-fixture-with-pylons
   using-fixture-with-appengine
   using-fixture-cmd
   using-temp-io
   
-----------------
API Documentation
-----------------

.. toctree::
   :glob:
   
   api/*

------
Status
------

fixture is a reimplementation of `testtools.fixtures`_ which was my first attempt at the idea.  As of July 2008 the fixture module is used in several test suites by my development teams at work.  One project is a data migration (ETL) framework using SQLObject and another is an in-house Pylons + Ext JS application using SQLAlchemy and Elixir.  It has been open source for a while but with only a few contributors so I'm not sure how much it's used outside of that.  

.. _testtools.fixtures : http://testtools.python-hosting.com/

.. _index-contact: 

-------
Contact
-------

Read on for info on submitting `issues`_.  For general discussion about fixture, how about the `Testing In Python`_ mailing list?  Otherwise, you can try me here: kumar.mcmillan @gmail.com

-------------------------------------
Where to submit issues, patches, bugs
-------------------------------------

Please submit any issues, patches, failing tests, and/or bugs using the `Issue
Tracker`_ on the `fixture project site`_.  If your code is used, your contribution will be
documented.

---------
Changelog
---------

- 1.1

  - Added support for loading data into the :mod:`Google App Engine Datastore <fixture.loadable.google_datastore_loadable>`
  - Added :func:`fixture.util.reset_log_level`
  - CHANGED the default log level to CRITICAL for all internal fixture logs so that they don't output gobs of debug code when some other module adds a handler to the root logger.
  - A couple bugs fixed

- 1.0
  
  - First release where :mod:`SQLAlchemy components <fixture.loadable.sqlalchemy_loadable>` worked well for 0.4, everything else was pretty stable

- 0.9 
  
  - First release where everything "kinda worked"

.. _Testing In Python: http://lists.idyll.org/listinfo/testing-in-python
.. _issues: http://code.google.com/p/fixture/issues/list
.. _Issue Tracker: http://code.google.com/p/fixture/issues/list
.. _fixture project site: http://code.google.com/p/fixture/
