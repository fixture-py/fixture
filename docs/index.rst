
==================
The fixture module
==================

.. contents::

Loading and referencing test data
---------------------------------

There are a couple ways to test an application that talks to a database.  You can create `mock objects`_ and concentrate entirely on `unit testing`_ the individual components, without testing the database layer itself, or you can simply load up sample data and run your application.  Thanks to `sqlite memory`_ databases, the latter may be more efficient than you think.  What's more important is that when you go to write a `functional test`_ (one that proves the interface to a feature works as expected) you achieve better `code coverage`_ and write less setup code if you take the sample data approach.

But it's easy enough to just instantiate model objects and insert data line by line in a setup function, right?  Or simply load a SQL file?  Yes, but this has two major downsides: you often have to worry about and manage complex chains of foreign keys; and when referencing data values later on, you either have to copy/paste the values or pass around lots of variables.

The fixture module simplifies this process by breaking it down into 2 components:

DataSet
    defines sets of sample data
Fixture
    knows how to load data

.. _mock objects: ...
.. _unit testing: ...
.. _sqlite memory: ...
.. _functional test: ...
.. _code coverage: ...

DataSet: defines sets of sample data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include_docstring:: fixture.dataset

Fixture: knows how to load data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include_docstring:: fixture.base

LoadableFixture: knows how to load data into something useful
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include_docstring:: fixture.loadable

The fixture command: generate DataSet classes from real data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include_docstring:: fixture.command.generate

TempIO: working with temporary file systems
-------------------------------------------

.. include_docstring:: fixture.io

