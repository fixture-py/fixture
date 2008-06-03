
"""Loadable fixtures

.. contents:: :local:

A DataSet class is loaded via some storage medium, say, an object that implements a `Data Mapper`_ or `Active Record`_ pattern.  A Fixture is an environment that knows how to load data using the right objects.  Behind the scenes, the rows and columns of the DataSet are simply passed off to the storage medium so that it can save the data.

.. _Data Mapper: http://www.martinfowler.com/eaaCatalog/dataMapper.html
.. _Active Record: http://www.martinfowler.com/eaaCatalog/activeRecord.html

Supported storage media
~~~~~~~~~~~~~~~~~~~~~~~

The Fixture class is designed to support many different types of storage media and there is a section later about creating your own Fixture.  Here are the various storage media supported by built-in Fixture subclasses:

SQLAlchemy
++++++++++

To ensure you are working with a compatible version of SQLAlchemy you can run ::

    easy_install fixture[sqlalchemy]

.. note::
    
    as of 1.0, fixture no longer supports SQLAlchemy less than version 0.4.  To work with SQLAlchemy 0.3, you will need `fixture 0.9`_
    
.. _fixture 0.9: http://farmdev.com/projects/fixture/0.9/docs/

DataSet classes can be loaded into `Table`_ objects or `mapped classes`_ via the `sqlalchemy`_ module::

    >>> from fixture import SQLAlchemyFixture
    >>> from sqlalchemy import *
    >>> from sqlalchemy.orm import *
    >>> from fixture.examples.db import sqlalchemy_examples
    >>> from fixture.examples.db.sqlalchemy_examples import metadata
    >>> metadata.bind = create_engine("sqlite:///:memory:")
    >>> metadata.create_all()
    >>> dbfixture = SQLAlchemyFixture(
    ...                 engine=metadata.bind, 
    ...                 env=sqlalchemy_examples)
    ... 

For more info see `SQLAlchemyFixture API`_

Elixir
++++++

DataSet class can be loaded into `Elixir entities`_ by using the SQLAlchemyFixture (see previous example).

**WARNING**: fixture uses its own scoped session to load data so that objects are separate from the application under test.  
This means you will need to configure all Elixir entities (and any classes mapped with ``Session.mapper()``) like so::

    class MyElixirEntity(Entity):
        # ...
        using_mapper_options(save_on_init=False)

Without this, fixture has no way of saving objects to its own session.

SQLObject
+++++++++

To ensure you are working with a compatible version of SQLObject you can run ::

    easy_install fixture[sqlobject]
    
DataSet classes can be loaded into `SQLObject classes`_ via the `sqlobject`_ module::

    >>> from fixture import SQLObjectFixture
    >>> from fixture.examples.db import sqlobject_examples
    >>> dbfixture = SQLObjectFixture(
    ...     dsn="sqlite:/:memory:", env=sqlobject_examples)
    ... 

For more info see `SQLObjectFixture API`_.

.. _SQLAlchemyFixture API: ../apidocs/fixture.loadable.sqlalchemy_loadable.SQLAlchemyFixture.html
.. _SQLObjectFixture API: ../apidocs/fixture.loadable.sqlobject_loadable.SQLObjectFixture.html

An Example Loading Data Using SQLAlchemy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fixture is designed for applications that already define a way of accessing its data; the LoadableFixture just "hooks in" to that interface.  To start this example, here is some `sqlalchemy`_ code to set up a database of books and authors::

    >>> from sqlalchemy import *
    >>> from sqlalchemy.orm import *
    >>> engine = create_engine('sqlite:////tmp/fixture_example.db')
    >>> metadata = MetaData()
    >>> metadata.bind = engine
    >>> Session = scoped_session(sessionmaker(bind=metadata.bind, autoflush=True, transactional=True))
    >>> session = Session()

Set up a place to store authors ...

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

Next set up a place to store books with each book having an author ...

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

::

    >>> metadata.create_all()

Consult the `sqlalchemy`_ documentation for further examples of data mapping.

.. _sqlalchemy: http://www.sqlalchemy.org/
.. _Table: http://www.sqlalchemy.org/docs/tutorial.myt#tutorial_schemasql_table_creating
.. _mapped classes: http://www.sqlalchemy.org/docs/datamapping.myt
.. _Elixir entities: http://elixir.ematia.de/
.. _sqlobject: http://sqlobject.org/
.. _SQLObject classes: http://sqlobject.org/SQLObject.html#declaring-the-class

Defining a Fixture
~~~~~~~~~~~~~~~~~~

This is a fixture with minimal configuration to support loading data into the Book or Author mapped classes::

    >>> from fixture import SQLAlchemyFixture
    >>> dbfixture = SQLAlchemyFixture(
    ...     env={'BookData': Book, 'AuthorData': Author},
    ...     engine=metadata.bind )
    ... 

- Any keyword attribute of a LoadableFixture can be set later on as an 
  attribute of the instance.
- LoadableFixture instances can safely be module-level objects
- An ``env`` can be a dict or a module
    
.. _session_context keyword: ../apidocs/fixture.loadable.sqlalchemy_loadable.SQLAlchemyFixture.html
.. _fixture.style.NamedDataStyle: ../apidocs/fixture.style.NamedDataStyle.html

Loading DataSet objects
~~~~~~~~~~~~~~~~~~~~~~~

To load some data for a test, you define it first in ``DataSet`` classes::

    >>> from fixture import DataSet
    >>> class AuthorData(DataSet):
    ...     class frank_herbert:
    ...         first_name = "Frank"
    ...         last_name = "Herbert"
    >>> class BookData(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author = AuthorData.frank_herbert

As you recall, we passed a dictionary into the Fixture that associates DataSet names with storage objects.  Using this dict, a ``Fixture.Data`` instance now knows to use the sqlalchemy mapped class ``Book`` when saving a DataSet named ``BookData``.

The ``Fixture.Data`` instance implements the ``setup()`` and ``teardown()`` methods typical to any test object.  At the beginning of a test the ``DataSet`` objects are loaded like so::
    
    >>> data = dbfixture.data(AuthorData, BookData)
    >>> data.setup() 

::

    >>> session.query(Book).all() #doctest: +ELLIPSIS
    [<...Book object at ...>]
    >>> all_books = session.query(Book).all()
    >>> all_books #doctest: +ELLIPSIS
    [<...Book object at ...>]
    >>> all_books[0].author.first_name
    u'Frank'

... And are removed like this::

    >>> data.teardown()
    >>> session.query(Book).all()
    []

Loading DataSet classes in a test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you have a Fixture object to load DataSet classes and you know how setup / teardown works, you are ready to write some tests.  You can either write your own code that creates a data instance and calls setup/teardown manually (like in previous examples), or you can use one of several utilities.  

Loading objects using DataTestCase
++++++++++++++++++++++++++++++++++

DataTestCase is a mixin class to use with Python's built-in ``unittest.TestCase``::

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

Re-using what was created earlier, the ``fixture`` attribute is set to the Fixture instance and the ``datasets`` attribute is set to a list of DataSet classes.  When in the test method itself, as you can see, you can reference loaded data through ``self.data``, an instance of SuperSet.  Keep in mind that if you need to override either setUp() or tearDown() then you'll have to call the super methods.

See the `DataTestCase API`_ for a full explanation of how it can be configured.

.. _DataTestCase API: ../apidocs/fixture.util.DataTestCase.html
    

Loading objects using @dbfixture.with_data
++++++++++++++++++++++++++++++++++++++++++

If you use nose_, a test runner for Python, then you may be familiar with its `discovery of test functions`_.  Test functions provide a quick way to write procedural tests and often illustrate more concisely what features are being tested.  Fixture provides a decorator method called ``@with_data`` that wraps around a test function so that data is loaded before the test.  If you don't have nose_ installed, simply install fixture like so and the correct version will be installed for you::
    
    easy_install fixture[decorators]

Load data for a test function like this::

    >>> @dbfixture.with_data(AuthorData, BookData)
    ... def test_books_are_in_stock(data):
    ...     session.query(Book).filter_by(title=data.BookData.dune.title).one()
    ... 
    >>> import nose
    >>> case = nose.case.FunctionTestCase(test_books_are_in_stock)
    >>> unittest.TextTestRunner().run(case)
    <unittest._TextTestResult run=1 errors=0 failures=0>

Like in the previous example, the ``data`` attribute is a SuperSet object you can use to reference loaded data.  This is passed to your decorated test method as its first argument.

See the `Fixture.Data.with_data API`_ for more information.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _discovery of test functions: http://code.google.com/p/python-nose/wiki/WritingTests
.. _Fixture.Data.with_data API: ../apidocs/fixture.base.Fixture.html#with_data

Loading objects using the with statement
++++++++++++++++++++++++++++++++++++++++

In Python 2.5 or later you can also load data for a test using the `with statement`_.  Anywhere in your code, when you enter a with block using a Fixture.Data instance, the data is loaded and you have an instance with which to reference the data.  When you exit the block, the data is torn down for you, regardless of whether there was an exception or not.  For example::

    from __future__ import with_statement
    with dbfixture.data(AuthorData, BookData) as data:
        session.query(Book).filter_by(title=self.data.BookData.dune.title).one()

.. _with statement: http://www.python.org/dev/peps/pep-0343/

Discovering storable objects with Style
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you didn't want to create a strict mapping of DataSet class names to their storable object names you can use Style objects to translate DataSet class names.  For example, consider this Fixture :

    >>> from fixture import SQLAlchemyFixture, TrimmedNameStyle
    >>> dbfixture = SQLAlchemyFixture(
    ...     env=globals(),
    ...     style=TrimmedNameStyle(suffix="Data"),
    ...     engine=metadata.bind )
    ... 

This would take the name ``AuthorData`` and trim off "Data" from its name to find ``Author``, its mapped sqlalchemy class for storing data.  Since this is a logical convention to follow for naming DataSet classes, you can use a shortcut:

    >>> from fixture import NamedDataStyle
    >>> dbfixture = SQLAlchemyFixture(
    ...     env=globals(),
    ...     style=NamedDataStyle(),
    ...     engine=metadata.bind )
    ... 

See the `Style API`_ for all available Style objects.

.. _Style API: ../apidocs/fixture.style.html

Defining a custom LoadableFixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's possible to create your own LoadableFixture if you need to load data with something other than SQLAlchemy or SQLObject.

You'll need to subclass at least `fixture.loadable.loadable:LoadableFixture`_, possibly even `fixture.loadable.loadable:EnvLoadableFixture`_ or the more useful `fixture.loadable.loadable:DBLoadableFixture`_.  Here is a simple example for creating a fixture that hooks into some kind of database-centric loading mechanism::

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

Now let's load some data into the custom Fixture using a simple ``env`` mapping::

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
    

.. _fixture.loadable.loadable:LoadableFixture: ../apidocs/fixture.loadable.loadable.LoadableFixture.html
.. _fixture.loadable.loadable:EnvLoadableFixture: ../apidocs/fixture.loadable.loadable.EnvLoadableFixture.html
.. _fixture.loadable.loadable:DBLoadableFixture: ../apidocs/fixture.loadable.loadable.DBLoadableFixture.html

.. api_only::
   The fixture.loadable module
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# from __future__ import with_statement
__all__ = ['LoadableFixture', 'EnvLoadableFixture', 'DBLoadableFixture', 'DeferredStoredObject']
import sys, types
from fixture.base import Fixture
from fixture.util import ObjRegistry, _mklog
from fixture.style import OriginalStyle
from fixture.dataset import Ref, dataset_registry, DataRow, is_rowlike
from fixture.exc import LoadError, UnloadError
import logging

log     = _mklog("fixture.loadable")
treelog = _mklog("fixture.loadable.tree")

class LoadableFixture(Fixture):
    """knows how to load data into something useful.
    
    This is an abstract class and cannot be used directly.  You can use a 
    LoadableFixture that already knows how to load into a specific medium, 
    such as SQLAlchemyFixture, or create your own to build your own to load 
    DataSet objects into custom storage media.

    Keyword Arguments
    -----------------
    - dataclass
    
      - class to instantiate with datasets (defaults to that of Fixture)

    - style

      - a Style object to translate names with (defaults to NamedDataStyle)
 
    - medium

      - optional LoadableFixture.StorageMediumAdapter to store DataSet 
        objects with
    
    """
    style = OriginalStyle()
    dataclass = Fixture.dataclass
    
    def __init__(self, style=None, medium=None, **kw):
        Fixture.__init__(self, loader=self, **kw)
        if style:
            self.style = style
        if medium:
            self.Medium = medium
    
    class StorageMediumAdapter(object):
        """common interface for working with storable objects.
        """
        def __init__(self, medium, dataset):
            self.medium = medium
            self.dataset = dataset
            self.transaction = None
        
        def __getattr__(self, name):
            return getattr(self.obj, name)
        
        def __repr__(self):
            return "%s at %s for %s" % (
                    self.__class__.__name__, hex(id(self)), self.medium)
            
        def clear(self, obj):
            """clear the stored object.
            """
            raise NotImplementedError
        
        def clearall(self):
            """clear all stored objects.
            """
            log.info("CLEARING stored objects for %s", self.dataset)
            for obj in self.dataset.meta._stored_objects:
                try:
                    self.clear(obj)
                except Exception, e:
                    etype, val, tb = sys.exc_info()
                    raise UnloadError(etype, val, self.dataset, 
                                         stored_object=obj), None, tb
            
        def save(self, row, column_vals):
            """given a DataRow, save it somehow.
            
            column_vals is an iterable of (column_name, column_value)
            """
            raise NotImplementedError
            
        def visit_loader(self, loader):
            """a chance to visit the LoadableFixture object."""
            pass
            
    Medium = StorageMediumAdapter
            
    class StorageMediaNotFound(LookupError):
        """Looking up a storable object failed."""
        pass
    
    class LoadQueue(ObjRegistry):
        """Keeps track of what class instances were loaded.
        
        "level" is used like so:
            
        The lower the level, the lower that object is on the foreign key chain.  
        As the level increases, this means more foreign objects depend on the 
        local object.  Thus, objects need to be unloaded starting at the lowest 
        level and working up.  Also, since objects can appear multiple times in 
        foreign key chains, the queue only acknowledges the object at its 
        highest level, since this will ensure all dependencies get unloaded 
        before it.  
        
        """

        def __init__(self):
            ObjRegistry.__init__(self)
            self.tree = {}
            self.limit = {}
        
        def __repr__(self):
            return "<%s at %s>" % (
                    self.__class__.__name__, hex(id(self)))
        
        def _pushid(self, id, level):
            if id in self.limit:
                # only store the object at its highest level:
                if level > self.limit[id]:
                    self.tree[self.limit[id]].remove(id)
                    del self.limit[id]
                else:
                    return
            self.tree.setdefault(level, [])
            self.tree[level].append(id)
            self.limit[id] = level
        
        def clear(self):
            ObjRegistry.clear(self)
            # this is an attempt to free up refs to database connections:
            self.tree = {}
            self.limit = {}
        
        def register(self, obj, level):
            """register this object as "loaded" at level
            """
            id = ObjRegistry.register(self, obj)
            self._pushid(id, level)
            return id
        
        def referenced(self, obj, level):
            """tell the queue that this object was referenced again at level.
            """
            id = self.id(obj)
            self._pushid(id, level)
        
        def to_unload(self):
            """yields a list of objects suitable for unloading.
            """
            level_nums = self.tree.keys()
            level_nums.sort()
            treelog.info("*** unload order ***")
            for level in level_nums:
                unload_queue = self.tree[level]
                verbose_obj = []
                
                for id in unload_queue:
                    obj = self.registry[id]
                    verbose_obj.append(obj.__class__.__name__)
                    yield obj
                
                treelog.info("%s. %s", level, verbose_obj)
    
    def attach_storage_medium(self, ds):
        raise NotImplementedError
    
    def begin(self, unloading=False):
        if not unloading:
            self.loaded = self.LoadQueue()
    
    def commit(self):
        raise NotImplementedError
    
    def load(self, data):
        def loader():
            for ds in data:
                self.load_dataset(ds)
        self.wrap_in_transaction(loader, unloading=False)
        
    def load_dataset(self, ds, level=1):
        """load this dataset and all its dependent datasets.
        
        level is essentially the order of processing (going from dataset to 
        dependent datasets).  Child datasets are always loaded before the 
        parent.  The level is important for visualizing the chain of 
        dependencies : 0 is the bottom, and thus should be the first set of 
        objects unloaded
        
        """
        is_parent = level==1
        
        levsep = is_parent and "/--------" or "|__.."
        treelog.info(
            "%s%s%s (%s)", level * '  ', levsep, ds.__class__.__name__, 
                                            (is_parent and "parent" or level))
        
        for ref_ds in ds.meta.references:
            r = ref_ds.shared_instance(default_refclass=self.dataclass)
            new_level = level+1
            self.load_dataset(r,  level=new_level)
        
        self.attach_storage_medium(ds)
        
        if ds in self.loaded:
            # keep track of its order but don't actually load it...
            self.loaded.referenced(ds, level)
            return
        
        log.info("LOADING rows in %s", ds)
        ds.meta.storage_medium.visit_loader(self)
        registered = False
        for key, row in ds:
            try:
                self.resolve_row_references(ds, row)
                if not isinstance(row, DataRow):
                    row = row(ds)
                def column_vals():
                    for c in row.columns():
                        yield (c, self.resolve_stored_object(getattr(row, c)))
                obj = ds.meta.storage_medium.save(row, column_vals())
                ds.meta._stored_objects.store(key, obj)
                # save the instance in place of the class...
                ds._setdata(key, row)
                if not registered:
                    self.loaded.register(ds, level)
                    registered = True
                
            except Exception, e:
                etype, val, tb = sys.exc_info()
                raise LoadError(etype, val, ds, key=key, row=row), None, tb
    
    def resolve_row_references(self, current_dataset, row):        
        """resolve this DataRow object's referenced values.
        """
        def resolved_rowlike(rowlike):
            key = rowlike.__name__
            if rowlike._dataset is type(current_dataset):
                return DeferredStoredObject(rowlike._dataset, key)
            loaded_ds = self.loaded[rowlike._dataset]
            return loaded_ds.meta._stored_objects.get_object(key)
        def resolve_stored_object(candidate):            
            if is_rowlike(candidate):
                return resolved_rowlike(candidate)
            else:
                # then it is the stored object itself.  this would happen if 
                # there is a reciprocal foreign key (i.e. organization has a 
                # parent organization)
                return candidate
                
        for name in row.columns():
            val = getattr(row, name)
            if type(val) in (types.ListType, types.TupleType):
                # i.e. categories = [python, ruby]
                setattr(row, name, map(resolve_stored_object, val))
            elif is_rowlike(val):
                # i.e. category = python
                setattr(row, name, resolved_rowlike(val))
            elif isinstance(val, Ref.Value):
                # i.e. category_id = python.id.
                ref = val.ref
                # now the ref will return the attribute from a stored object 
                # when __get__ is invoked
                ref.dataset_obj = self.loaded[ref.dataset_class]
    
    def rollback(self):
        raise NotImplementedError
    
    def then_finally(self, unloading=False):
        pass
    
    def unload(self):
        def unloader():
            for dataset in self.loaded.to_unload():
                self.unload_dataset(dataset)
            self.loaded.clear()
            dataset_registry.clear()
        self.wrap_in_transaction(unloader, unloading=True)
    
    def unload_dataset(self, dataset):
        dataset.meta.storage_medium.clearall()
    
    def wrap_in_transaction(self, routine, unloading=False):
        self.begin(unloading=unloading)
        try:
            try:
                routine()
            except:
                self.rollback()
                raise
            else:
                self.commit()
        finally:
            self.then_finally(unloading=unloading)

class EnvLoadableFixture(LoadableFixture):
    """An abstract fixture that can resolve DataSet objects from an env.
    
    Keyword "env" should be a dict or a module if not None.
    According to the style rules, the env will be used to find objects by name.
    
    """
    def __init__(self, env=None, **kw):
        LoadableFixture.__init__(self, **kw)
        self.env = env
    
    def attach_storage_medium(self, ds):
        if ds.meta.storage_medium is not None:
            # already attached...
            return
        
        storable = ds.meta.storable
        
        if not storable:
            if not ds.meta.storable_name:
                ds.meta.storable_name = self.style.guess_storable_name(
                                                        ds.__class__.__name__)
        
            if hasattr(self.env, 'get'):
                storable = self.env.get(ds.meta.storable_name, None)
            if not storable:
                if hasattr(self.env, ds.meta.storable_name):
                    try:
                        storable = getattr(self.env, ds.meta.storable_name)
                    except AttributeError:
                        pass
        
            if not storable:
                repr_env = repr(type(self.env))
                if hasattr(self.env, '__module__'):
                    repr_env = "%s from '%s'" % (repr_env, self.env.__module__)
                
                raise self.StorageMediaNotFound(
                    "could not find %s '%s' for "
                    "dataset %s in self.env (%s)" % (
                        self.Medium, ds.meta.storable_name, ds, repr_env))
                        
        if storable == ds.__class__:
            raise ValueError(
                "cannot use %s %s as a storable object of itself! "
                "(perhaps your style object was not configured right?)" % (
                                        ds.__class__.__name__, ds.__class__))
        ds.meta.storage_medium = self.Medium(storable, ds)
        
    def resolve_stored_object(self, column_val):
        if type(column_val)==DeferredStoredObject:
            return column_val.get_stored_object_from_loader(self)
        else:
            return column_val

class DBLoadableFixture(EnvLoadableFixture):
    """An abstract fixture that will be loadable into a database.
    
    More specifically, one that forces its implementation to run atomically 
    (within a begin/ commit/ rollback block).
    """
    def __init__(self, dsn=None, **kw):
        EnvLoadableFixture.__init__(self, **kw)
        self.dsn = dsn
        self.transaction = None
    
    def begin(self, unloading=False):
        EnvLoadableFixture.begin(self, unloading=unloading)
        self.transaction = self.create_transaction()
    
    def commit(self):
        self.transaction.commit()
    
    def create_transaction(self):
        raise NotImplementedError
    
    def rollback(self):
        self.transaction.rollback()

class DeferredStoredObject(object):
    """A stored representation of a row in a DatSet, deferred.
    
    The actual stored object can only be resolved by the StoredMediumAdapter 
    itself
    
    Imagine...::
    
        >>> from fixture import DataSet
        >>> class PersonData(DataSet):
        ...     class adam:
        ...         father=None
        ...     class eve:
        ...         father=None
        ...     class jenny:
        ...         pass
        ...     jenny.father = adam
        ... 
    
    This would be a way to indicate that jenny's father is adam.  This class 
    will encapsulate that reference so it can be resolved as close to when it 
    was created as possible.
    
    """
    def __init__(self, dataset, key):
        self.dataset = dataset
        self.key = key
    
    def get_stored_object_from_loader(self, loader):
        loaded_ds = loader.loaded[self.dataset]
        return loaded_ds.meta._stored_objects.get_object(self.key)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
