
.. _using-dataset:

-------------
Using DataSet
-------------

.. contents:: :local:

Before loading data, you need to define it. A single subclass of
:class:`DataSet <fixture.dataset.DataSet>` represents a database relation in Python code. Think of the class as a
table, each inner class as a row, and each attribute per row as a column value.
For example:

.. doctest::

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
so).  How you create a :class:`DataSet <fixture.dataset.DataSet>` will be influenced by how the underlying data object saves data.

Inheriting DataSet rows
~~~~~~~~~~~~~~~~~~~~~~~

Since a row is just a Python class, you can inherit from a row to morph its values, i.e.:

.. doctest::

    >>> class Authors(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"
    ...     class brian_herbert(frank_herbert):
    ...         first_name = "Brian"

This is useful for keeping code simple and hand-coding foreign key dependencies.

.. note::
    The primary key value will not be inherited from a row.  See 
    `Customizing a DataSet`_ if you need to set the name of a DataSet's primary 
    key to something other than ``id``.

Referencing foreign DataSet classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When defining rows in a :class:`DataSet <fixture.dataset.DataSet>` that reference foreign keys, you need to mimic how your data object wants to save such a reference.  If your data object wants to save foreign keys as objects (not ID numbers) then you can simply reference another row in a :class:`DataSet <fixture.dataset.DataSet>` as if it were an object.:

.. doctest::

    >>> class Books(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author = Authors.frank_herbert
    ...     class sudanna:
    ...         title = "Sudanna Sudanna"
    ...         author = Authors.brian_herbert

During data loading, the reference to DataSet ``Authors.brian_herbert`` will be replaced with the actual stored object used to load that row into the database.  This will work as expected for one-to-many relationships, i.e.:

.. doctest::

    >>> class Books(DataSet):
    ...     class two_worlds:
    ...         title = "Man of Two Worlds"
    ...         authors = [Authors.frank_herbert, Authors.brian_herbert]

However, in some cases you may need to reference an attribute that does not have a value until it is loaded, like a serial ID column.  (Note that this is not supported by the `SQLAlchemy`_ data layer when using sessions.)  To facilitate this, each inner class of a :class:`DataSet <fixture.dataset.DataSet>` gets decorated with a special method, :class:`ref() <fixture.dataset.Ref>`,
that can be used to reference a column value before it exists, i.e.:

.. doctest::

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

.. _using-dataset-to-json:

Converting a DataSet to JSON
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can dump a `JSON <http://www.json.org/>`_ (JavaScript Object Notation) encoded representation of the data in a DataSet class with the method :func:`fixture.dataset.converter.dataset_to_json`.  This feature was added to test AJAX user interface components.  The JSON formatted string can be used as a stub response that a server might return to the UI component.

If you're on Python less than 2.6, you'll need to install `simplejson <http://code.google.com/p/simplejson>`_::
    
    easy_install simplejson

Given the following DataSet:

.. doctest::

    >>> from fixture import DataSet
    >>> class ArtistData(DataSet):
    ...     class joan_jett:
    ...         name = "Joan Jett and the Black Hearts"
    ...     class ramones:
    ...         name = "The Ramones"
    ... 

Convert it to a JSON string with :func:`dataset_to_json <fixture.dataset.converter.dataset_to_json>`:

.. doctest::
    
    >>> from fixture.dataset.converter import dataset_to_json
    >>> dataset_to_json(ArtistData)
    '[{"name": "Joan Jett and the Black Hearts"}, {"name": "The Ramones"}]'

The DataSet is converted to a list of dictionaries appearing in 
alphabetical order of inner class name.  Only the inner class 
attributes / values are used to create each dictionary.  
The inner class names -- ``joan_jett``, etc -- are ignored.

To customize the JSON you can also define the ``wrap`` keyword: a callable 
that takes one argument, the list of dictionaries, and returns a new JSON 
serializable object.  For example:

.. doctest::
    
    >>> def wrap_in_dict(objects):
    ...     return {'data': objects}
    ... 
    >>> dataset_to_json(ArtistData, wrap=wrap_in_dict) # doctest:+ELLIPSIS
    '{"data": [{"name": "Joan Jett and the Black Hearts"}, ...]}'

For all available keyword arguments, see API docs for :func:`dataset_to_json <fixture.dataset.converter.dataset_to_json>`.

.. note::
    
    Converting a dataset to JSON does not load the data into a database.  This means that any 
    attributes your tests might lazily access (like automatically incremented ID numbers) would not be available.

Customizing a Dataset
~~~~~~~~~~~~~~~~~~~~~

A :class:`DataSet <fixture.dataset.DataSet>` can be customized by defining a special inner class named ``Meta``.
See the :class:`DataSet.Meta <fixture.dataset.DataSetMeta>` API for more info.

API Documentation
~~~~~~~~~~~~~~~~~

See the :mod:`fixture.dataset` and :mod:`fixture.dataset.converter` module APIs.

