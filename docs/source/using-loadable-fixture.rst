.. _using-loadable-fixture:

---------------------
Using LoadableFixture
---------------------

.. contents:: :local:

A :class:`DataSet <fixture.dataset.DataSet>` class is loaded via some storage medium, say, an object that implements a `Data Mapper`_ or `Active Record`_ pattern.  A Fixture is an environment that knows how to load data using the right objects.  Behind the scenes the rows and columns of the :class:`DataSet <fixture.dataset.DataSet>` are simply passed to the storage medium so that it can save the data.

.. _Data Mapper: http://www.martinfowler.com/eaaCatalog/dataMapper.html
.. _Active Record: http://www.martinfowler.com/eaaCatalog/activeRecord.html

Supported storage media
~~~~~~~~~~~~~~~~~~~~~~~

The Fixture class is designed to support many different types of databases and other storage media by hooking into 3rd party libraries that know how to work with that media.  There is also a section later about creating your own Fixture.  Here are the various modules supported by built-in Fixture subclasses:

SQLAlchemy
++++++++++

To ensure you are working with a compatible version of SQLAlchemy you can run ::

    easy_install 'fixture[sqlalchemy]'

.. note::
    
    As of 1.0, fixture no longer supports SQLAlchemy less than version 0.4.  To work with SQLAlchemy 0.3 or earlier you will need `fixture 0.9`_
    
.. _fixture 0.9: http://farmdev.com/projects/fixture/0.9/docs/

DataSet classes can be loaded into `Table`_ objects or `mapped classes`_ via the `SQLAlchemy`_ module:

.. testsetup:: loading

    import os
    if os.path.exists('/tmp/fixture_example.db'):
        os.unlink('/tmp/fixture_example.db')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'fixture.test.test_loadable.test_django.project.settings'
    from fixture.test.test_loadable.test_django.project.app import models

.. doctest:: loading

    >>> from fixture import SQLAlchemyFixture
    >>> from sqlalchemy import *
    >>> from sqlalchemy.orm import *
    >>> from fixture.examples.db import sqlalchemy_examples
    >>> from fixture.examples.db.sqlalchemy_examples import metadata
    >>> metadata.bind = create_engine("sqlite:////tmp/fixture_example.db")
    >>> metadata.create_all()
    >>> dbfixture = SQLAlchemyFixture(
    ...                 engine=metadata.bind, 
    ...                 env=sqlalchemy_examples)
    ... 

Read on for a complete example or see :class:`SQLAlchemyFixture API <fixture.loadable.sqlalchemy_loadable.SQLAlchemyFixture>` for details.

Elixir
++++++

DataSet class can be loaded into `Elixir entities`_ by using the SQLAlchemyFixture (see previous example).

**WARNING**: fixture uses its own scoped session to load data so that objects are separate from the application under test.  
This means you will need to configure all Elixir entities (and any classes mapped with `Session.mapper() <http://www.sqlalchemy.org/docs/04/session.html#unitofwork_contextual_associating>`_) like so::

    class MyElixirEntity(Entity):
        # ...
        using_mapper_options(save_on_init=False)

Without this, fixture has no way of saving objects to its own session.  To use Elixir entities without specifiying ``save_on_init=False`` you would have to share the fixture session in Elixir.  You can get the fixture session like this:

.. doctest:: loading

    >>> from fixture.loadable.sqlalchemy_loadable import Session
    >>> app_session = Session()

There are several ways to assign a session to Elixir, one of which is simply::
    
    elixir.session = app_session

SQLObject
+++++++++

To ensure you are working with a compatible version of SQLObject you can run ::

    easy_install 'fixture[sqlobject]'
    
DataSet classes can be loaded into `SQLObject classes`_ via the `sqlobject`_ module:

.. doctest:: loading

    >>> from fixture import SQLObjectFixture
    >>> from fixture.examples.db import sqlobject_examples
    >>> dbfixture = SQLObjectFixture(
    ...     dsn="sqlite:/:memory:", env=sqlobject_examples)
    ... 

See :class:`SQLObjectFixture API <fixture.loadable.sqlobject_loadable.SQLObjectFixture>` for details.

Google Datastore
++++++++++++++++

To load data for testing a `Google App Engine`_ site you'll need the `SDK <http://code.google.com/appengine/downloads.html>`_ installed locally.

DataSet classes can be loaded into `Datastore Entities`_ directly.

.. doctest:: loading

    >>> from fixture import GoogleDatastoreFixture
    >>> datafixture = GoogleDatastoreFixture(env=globals())
    
For a complete example, see :ref:`Using Fixture With Google App Engine <using-fixture-with-appengine>`.

For reference, also see :class:`GoogleDatastoreFixture API <fixture.loadable.google_datastore_loadable.GoogleDatastoreFixture>`.

.. _Datastore Entities: http://code.google.com/appengine/docs/datastore/entitiesandmodels.html

Django
++++++

Django support for loading datasets work with `django version 1.0.2 <http://www.djangoproject.com/download/>`_. Here's a quick example of how you use it:

.. currentmodule:: fixture.loadable.django_loadable

.. doctest:: loading

    >>> from fixture import DjangoFixture
    >>> from fixture.style import NamedDataStyle
    >>> django_fixture = DjangoFixture()
    
By default :class:`~DjangoFixture` uses a special class for it's env (:class:`~DjangoEnv`). If as above you don't pass in an env keyword arguement :class:`~DjangoFixture` will use this class to resolve fixtures to models. You can of course still pass an env and style if you want to change this, see :ref:`using-loadable-fixture-style` for more details

For more info see :mod:`~fixture.loadable.django_loadable` especially :class:`~DjangoFixture` and the more extended guide: :ref:`using-fixture-with-django`

An Example of Loading Data Using SQLAlchemy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fixture is designed for applications that already have a way to store data; the :class:`LoadableFixture <fixture.loadable.loadable.LoadableFixture>` just hooks in to that interface.  To start this example, here is some `SQLAlchemy`_ code to set up a database of books and authors:

.. doctest:: loading

    >>> from sqlalchemy import *
    >>> from sqlalchemy.orm import *
    >>> engine = create_engine('sqlite:////tmp/fixture_example.db')
    >>> metadata = MetaData()
    >>> metadata.bind = engine
    >>> Session = scoped_session(sessionmaker(bind=metadata.bind, autoflush=True, transactional=True))
    >>> session = Session()

Set up the table and mapper for authors ...

.. doctest:: loading

    >>> authors = Table('authors', metadata,
    ...     Column('id', Integer, primary_key=True),
    ...     Column('first_name', String(60)),
    ...     Column('last_name', String(60)))
    ... 
    >>> class Author(object):
    ...     pass
    ... 
    >>> mapper(Author, authors) #doctest: +ELLIPSIS
    <sqlalchemy.orm.mapper.Mapper object at ...>

Next set up the table and mapper for books with each book having an author ...

.. doctest:: loading

    >>> books = Table('books', metadata, 
    ...     Column('id', Integer, primary_key=True),
    ...     Column('title', String(30)),
    ...     Column('author_id', Integer, ForeignKey('authors.id')))
    ... 
    >>> class Book(object):
    ...     pass
    ... 
    >>> mapper(Book, books, properties={
    ...     'author': relation(Author, backref='books')
    ... }) #doctest: +ELLIPSIS
    <sqlalchemy.orm.mapper.Mapper object at ...>

.. doctest:: loading

    >>> metadata.create_all()

Consult the `SQLAlchemy`_ documentation for further examples of data mapping.

.. _Google App Engine: http://code.google.com/appengine/
.. _sqlalchemy: http://www.sqlalchemy.org/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Table: http://www.sqlalchemy.org/docs/tutorial.myt#tutorial_schemasql_table_creating
.. _mapped classes: http://www.sqlalchemy.org/docs/datamapping.myt
.. _Elixir entities: http://elixir.ematia.de/
.. _sqlobject: http://sqlobject.org/
.. _SQLObject classes: http://sqlobject.org/SQLObject.html#declaring-the-class

Defining a Fixture
~~~~~~~~~~~~~~~~~~

This is a fixture with minimal configuration to support loading data into the ``Book`` or ``Author`` mapped classes:

.. doctest:: loading

    >>> from fixture import SQLAlchemyFixture
    >>> dbfixture = SQLAlchemyFixture(
    ...     env={'BookData': Book, 'AuthorData': Author},
    ...     engine=metadata.bind )
    ... 

- Any keyword attribute of a :class:`LoadableFixture <fixture.loadable.loadable.LoadableFixture>` can be set later on as an 
  attribute of the instance.
- :class:`LoadableFixture <fixture.loadable.loadable.LoadableFixture>` instances can safely be module-level objects
- An ``env`` can be a dict or a module.  See :meth:`EnvLoadableFixture.attach_storage_medium <fixture.loadable.loadable.EnvLoadableFixture.attach_storage_medium>` for details.

Loading DataSet objects
~~~~~~~~~~~~~~~~~~~~~~~

To load some data for a test, you define it first in DataSet classes:

.. doctest:: loading

    >>> from fixture import DataSet
    >>> class AuthorData(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"
    >>> class BookData(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author = AuthorData.frank_herbert

As you recall, we passed a dictionary into the Fixture that associates :class:`DataSet <fixture.dataset.DataSet>` names with storage objects.  Using this dict, a :class:`FixtureData <fixture.base.FixtureData>` instance now knows to use the sqlalchemy mapped class ``Book`` when saving a DataSet named ``BookData``.

The ``Fixture.Data`` instance implements the ``setup()`` and ``teardown()`` methods typical to any test object.  At the beginning of a test the ``DataSet`` objects are loaded like so:
    
.. doctest:: loading

    >>> data = dbfixture.data(AuthorData, BookData)
    >>> data.setup() 

.. doctest:: loading

    >>> session.query(Book).all() #doctest: +ELLIPSIS
    [<...Book object at ...>]
    >>> all_books = session.query(Book).all()
    >>> all_books #doctest: +ELLIPSIS
    [<...Book object at ...>]
    >>> all_books[0].author.first_name
    u'Frank'

and are removed like this:

.. doctest:: loading

    >>> data.teardown()
    >>> session.query(Book).all()
    []

Loading DataSet classes in a test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you have a Fixture object to load :class:`DataSet <fixture.dataset.DataSet>` classes and you know how setup / teardown works, you are ready to write some tests.  You can either write your own code that creates a data instance and calls setup / teardown manually (like in previous examples), or you can use one of several utilities.  

Loading objects using DataTestCase
++++++++++++++++++++++++++++++++++

DataTestCase is a mixin class to use with Python's built-in ``unittest.TestCase``:

.. doctest:: loading

    >>> import unittest
    >>> from fixture import DataTestCase
    >>> class TestBookShop(DataTestCase, unittest.TestCase):
    ...     fixture = dbfixture
    ...     datasets = [BookData]
    ...
    ...     def test_books_are_in_stock(self):
    ...         b = session.query(Book).filter_by(title=self.data.BookData.dune.title).one()
    ...         assert b
    ... 
    >>> suite = unittest.TestLoader().loadTestsFromTestCase(TestBookShop)
    >>> unittest.TextTestRunner().run(suite)
    <unittest._TextTestResult run=1 errors=0 failures=0>

Re-using what was created earlier, the ``fixture`` attribute is set to the Fixture instance and the ``datasets`` attribute is set to a list of :class:`DataSet <fixture.dataset.DataSet>` classes.  When in the test method itself, as you can see, you can reference loaded data through ``self.data``, an instance of SuperSet.  Keep in mind that if you need to override either ``setUp()`` or ``tearDown()`` then you'll have to call the super methods.

See the :class:`fixture.util.DataTestCase` API for a full explanation of how it can be configured.
    

Loading objects using @dbfixture.with_data
++++++++++++++++++++++++++++++++++++++++++

If you use nose_, a test runner for Python, then you may be familiar with its `discovery of test functions`_.  Test functions provide a quick way to write procedural tests and often illustrate more concisely what features are being tested.  Fixture provides a decorator method called :meth:`@fixture.with_data <fixture.base.Fixture.with_data>` that wraps around a test function so that data is loaded before the test.  If you don't have nose_ installed, simply install fixture like so and the correct version will be installed for you::
    
    easy_install fixture[decorators]

Load data for a test function like this:

.. doctest:: loading

    >>> @dbfixture.with_data(AuthorData, BookData)
    ... def test_books_are_in_stock(data):
    ...     session.query(Book).filter_by(title=data.BookData.dune.title).one()
    ... 
    >>> import nose
    >>> case = nose.case.FunctionTestCase(test_books_are_in_stock)
    >>> unittest.TextTestRunner().run(case)
    <unittest._TextTestResult run=1 errors=0 failures=0>

Like in the previous example, the ``data`` attribute is a :class:`SuperSet <fixture.dataset.SuperSet>` object you can use to reference loaded data.  This is passed to your decorated test method as its first argument.

See the :meth:`Fixture.with_data <fixture.base.Fixture.with_data>` API for more information.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _discovery of test functions: http://code.google.com/p/python-nose/wiki/WritingTests

Loading objects using the with statement
++++++++++++++++++++++++++++++++++++++++

In Python 2.5 or later you can also load data for a test using the with statement (:pep:`343`).  Anywhere in your code, when you enter a with block using a :class:`FixtureData <fixture.base.FixtureData>` instance, the data is loaded and you have an instance with which to reference the data.  When you exit the block, the data is torn down for you, regardless of whether there was an exception or not.  For example::

    from __future__ import with_statement
    with dbfixture.data(AuthorData, BookData) as data:
        session.query(Book).filter_by(title=self.data.BookData.dune.title).one()

.. _using-loadable-fixture-style:

Discovering storable objects with Style
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you didn't want to create a strict mapping of :class:`DataSet <fixture.dataset.DataSet>` class names to their storable object names you can use :class:`Style <fixture.style.Style>` objects to translate DataSet class names.  For example, consider this Fixture :

.. doctest:: loading

    >>> from fixture import SQLAlchemyFixture, TrimmedNameStyle
    >>> dbfixture = SQLAlchemyFixture(
    ...     env=globals(),
    ...     style=TrimmedNameStyle(suffix="Data"),
    ...     engine=metadata.bind )
    ... 

This would take the name ``AuthorData`` and trim off "Data" from its name to find ``Author``, its mapped SQLAlchemy_ class for storing data.  Since this is a logical convention to follow for naming :class:`DataSet <fixture.dataset.DataSet>` classes, you can use a shortcut:

.. doctest:: loading

    >>> from fixture import NamedDataStyle
    >>> dbfixture = SQLAlchemyFixture(
    ...     env=globals(),
    ...     style=NamedDataStyle(),
    ...     engine=metadata.bind )
    ... 

See the :mod:`Style API <fixture.style>` for all available Style objects.

Defining a custom LoadableFixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's possible to create your own :class:`LoadableFixture <fixture.loadable.loadable:LoadableFixture>` if you need to load data with something other than SQLAlchemy_ or SQLObject_.

You'll need to subclass at least :class:`LoadableFixture <fixture.loadable.loadable:LoadableFixture>`, possibly even :class:`EnvLoadableFixture <fixture.loadable.loadable:EnvLoadableFixture>` or the more useful :class:`DBLoadableFixture <fixture.loadable.loadable:DBLoadableFixture>`.  Here is a simple example for creating a fixture that hooks into some kind of database-centric loading mechanism:

.. doctest:: loading

    >>> loaded_items = set()
    >>> class Author(object):
    ...     '''This would be your actual storage object, i.e. data mapper.
    ...        For the sake of brevity, you'll have to imagine that it knows 
    ...        how to somehow store "author" data.'''
    ... 
    ...     name = None # gets set by the data set
    ... 
    ...     def save(self):
    ...         '''just one example of how to save your object.
    ...            there is no signature guideline for how this object 
    ...            should save itself (see the adapter below).'''
    ...         loaded_items.add(self)
    ...     def __repr__(self):
    ...         return "<%s name=%s>" % (self.__class__.__name__, self.name)
    ...
    >>> from fixture.loadable import DBLoadableFixture
    >>> class MyFixture(DBLoadableFixture):
    ...     '''This is the class you will instantiate, the one that knows how to 
    ...        load datasets'''
    ... 
    ...     class Medium(DBLoadableFixture.Medium):
    ...         '''This is an object that adapts a Fixture storage medium 
    ...            to the actual storage medium.'''
    ... 
    ...         def clear(self, obj):
    ...             '''where you need to expunge the obj'''
    ...             loaded_items.remove(obj)
    ... 
    ...         def visit_loader(self, loader):
    ...             '''a chance to reference any attributes from the loader.
    ...                this is called before save().'''
    ... 
    ...         def save(self, row, column_vals):
    ...             '''save data into your object using the provided 
    ...                fixture.dataset.DataRow instance'''
    ...             # instantiate your real object class (Author), which was set 
    ...             # in __init__ to self.medium ...
    ...             obj = self.medium() 
    ...             for c, val in column_vals:
    ...                 # column values become object attributes...
    ...                 setattr(obj, c, val)
    ...             obj.save()
    ...             # be sure to return the object:
    ...             return obj
    ... 
    ...     def create_transaction(self):
    ...         '''a chance to create a transaction.
    ...            two separate transactions are used: one during loading
    ...            and another during unloading.'''
    ...         class DummyTransaction(object):
    ...             def begin(self):
    ...                 pass
    ...             def commit(self): 
    ...                 pass
    ...             def rollback(self): 
    ...                 pass
    ...         t = DummyTransaction()
    ...         t.begin() # you must call begin yourself, if necessary
    ...         return t
    >>> 

Now let's load some data into the custom Fixture using a simple ``env`` mapping:

.. doctest:: loading

    >>> from fixture import DataSet
    >>> class AuthorData(DataSet):
    ...     class frank_herbert:
    ...         name="Frank Herbert"
    ...
    >>> fixture = MyFixture(env={'AuthorData': Author})
    >>> data = fixture.data(AuthorData)
    >>> data.setup()
    >>> loaded_items
    set([<Author name=Frank Herbert>])
    >>> data.teardown()
    >>> loaded_items
    set([])

API Documentation
~~~~~~~~~~~~~~~~~

- :mod:`fixture.loadable`
- :mod:`fixture.loadable.sqlalchemy_loadable`
- :mod:`fixture.loadable.sqlobject_loadable`
