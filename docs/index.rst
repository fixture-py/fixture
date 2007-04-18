
========================
Using the fixture module
========================

.. contents::

------------------
Download / Install
------------------

Using the easy_install_ command::

    easy_install fixture

Or, if you want to create a link to the source without installing anything, cd into the root directory and type::

    python setup.py develop

Or ... if you're old school, this works with or without setuptools_::

    python setup.py install

.. note::
    The above commands may require root access

.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools

---------------------------------
Loading and referencing test data
---------------------------------

There are a couple ways to test a database-backed application.  You can create `mock objects`_ and concentrate entirely on `unit testing`_ individual components without testing the database layer itself, or you can simply load up sample data before you run a test.  Thanks to ``sqlite`` in-memory connections (a special DSN, ``sqlite:///:memory:``), the latter may be more efficient than you think.  What's more important is that when you create a `functional test`_ (one that proves the interface to a feature works as expected), testing with real data can help you achieve better `code coverage`_.

But it's easy enough to insert data line by line in a setup function, right?  Or simply load a SQL file?  Yes, but this has two major downsides: you often have to worry about and manage complex chains of foreign keys manually; and when referencing data values later on, you either have to copy/paste the values or pass around lots of variables.

The fixture module simplifies this by focusing on two independent components:

DataSet
    defines sets of sample data
Fixture
    knows how to load data

The details of loading the actual data is left up to your application's database layer itself (more info on this later).

.. _mock objects: http://en.wikipedia.org/wiki/Mock_object
.. _unit testing: http://en.wikipedia.org/wiki/Unit_testing
.. _functional test: http://en.wikipedia.org/wiki/Functional_test
.. _code coverage: http://en.wikipedia.org/wiki/Code_coverage

Using DataSet
-------------

.. include_docstring:: fixture.dataset

Using LoadableFixture
---------------------

.. include_docstring:: fixture.loadable

Using the fixture command
-------------------------

.. include_docstring:: fixture.command.generate

------------------------------------
Testing with a temporary file system
------------------------------------

.. include_docstring:: fixture.io

-----------------
API Documentation
-----------------

`See API documentation`_ for detailed documentation of individual ``fixture`` components

.. _See API documentation: ../apidocs/index.html

-------------------------------------
Where to submit issues, patches, bugs
-------------------------------------

Please submit any issues, patches, failing tests, and/or bugs using the `Issue
Tracker`_ on the `fixture project site`_. Even vague ideas for improvement will
be gladly accepted. If your code is included, your contribution will be
documented.

.. _Issue Tracker: http://code.google.com/p/fixture/issues/list
.. _fixture project site: http://code.google.com/p/fixture/
