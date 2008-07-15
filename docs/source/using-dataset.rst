
-------------
Using DataSet
-------------

.. contents:: :local:

Before loading data, you need to define it. A single subclass of
DataSet represents a database relation in Python code. Think of the class as a
table, each inner class as a row, and each attribute per row as a column value.
For example::

    >>> from fixture import DataSet
    >>> class Authors(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"

The inner class ``frank_herbert`` defines a row with the columns ``first_name``
and ``last_name``. The name ``frank_herbert`` is an identifier that you can use
later on, when you want to refer to this specific row.

The main goal will be to load this data into something useful, like a database.
But notice that the ``id`` values aren't defined in the DataSet. This is because
the database will most likely create an ``id`` for you when you insert the row 
(however, if you need to specify a specific ``id`` number, you are free to do 
so).  How you create a DataSet will be influenced by how the underlying data object saves data.

Inheriting DataSet rows
~~~~~~~~~~~~~~~~~~~~~~~

Since a row is just a Python class, you can inherit from a row to morph its values, i.e.::

    >>> class Authors(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"
    ...     class brian_herbert(frank_herbert):
    ...         first_name = "Brian"

This is useful for adhering to the DRY principle (Don't Repeat Yourself) as well
as for `testing edge cases`_.

.. note::
    The primary key value will not be inherited from a row.  See 
    `Customizing a DataSet`_ if you need to set the name of a DataSet's primary 
    key to something other than ``id``.

Referencing foreign DataSet classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When defining rows in a DataSet that reference foreign keys, you need to mimic how your data object wants to save such a reference.  If your data object wants to save foreign keys as objects (not ID numbers) then you can simply reference another row in a DataSet as if it were an object.::

    >>> class Books(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author = Authors.frank_herbert
    ...     class sudanna:
    ...         title = "Sudanna Sudanna"
    ...         author = Authors.brian_herbert

During data loading, the reference to DataSet ``Authors.brian_herbert`` will be replaced with the actual stored object used to load that row into the database.  This will work as expected for one-to-many relationships, i.e.::

    >>> class Books(DataSet):
    ...     class two_worlds:
    ...         title = "Man of Two Worlds"
    ...         authors = [Authors.frank_herbert, Authors.brian_herbert]

However, in some cases you may need to reference an attribute that does not have a value until it is loaded, like a serial ID column.  (Note that this is not supported by the `SQLAlchemy`_ data layer when using sessions.)  To facilitate this, each inner class of a DataSet gets decorated with a special method, ``ref()``,
that can be used to reference a column value before it exists, i.e.::

    >>> class Books(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author_id = Authors.frank_herbert.ref('id')
    ...     class sudanna:
    ...         title = "Sudanna Sudanna"
    ...         author_id = Authors.brian_herbert.ref('id')

.. _SQLAlchemy: http://www.sqlalchemy.org/

This sets the ``author_id`` to the ``id`` of another row in ``Author``, as if it
were a foreign key. But notice that the ``id`` attribute wasn't explicitly
defined by the ``Authors`` data set. When the ``id`` attribute is accessed later
on, its value is fetched from the actual row inserted.

Customizing a Dataset
~~~~~~~~~~~~~~~~~~~~~

A DataSet can be customized by defining a special inner class named ``Meta``.
See the `DataSet.Meta`_ API for more info.

.. _DataSet.Meta: ../apidocs/fixture.dataset.DataSet.Meta.html
.. _testing edge cases: http://brian.pontarelli.com/2006/12/04/the-importance-of-edge-case-testing/
