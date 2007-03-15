
"""Loadable fixtures

.. contents::

After defining data with the DataSet class you need some way to load the data for your test.  Each DataSet you want to load needs some storage medium, say, a `Data Mapper`_ or `Active Record`_ object.  A Fixture is simply an environment that knows how to load data using the right objects.  It puts the pieces together, if you will.

.. _Data Mapper: http://www.martinfowler.com/eaaCatalog/dataMapper.html
.. _Active Record: http://www.martinfowler.com/eaaCatalog/activeRecord.html

Supported storage media
-----------------------

To create a specific data-loading environment, the following subclasses are available:

SQLAlchemyFixture
    loads data using `Table`_ objects or `mapped classes`_ via the `sqlalchemy`_ 
    module
SQLObjectFixture
    loads data using `SQLObject classes`_ via the `sqlobject`_ module

The idea is that you application already defines its own way of accessing its data; the LoadableFixture just "hooks in" to that interface.  Before considering the Fixture, here is an example data model defined using `sqlalchemy`_::

    >>> from sqlalchemy import *
    >>> engine = create_engine('sqlite:///:memory:')
    >>> meta = BoundMetaData(engine)
    >>> session = create_session(engine)
    >>> authors = Table('authors', meta,
    ...     Column('id', Integer, primary_key=True),
    ...     Column('first_name', String),
    ...     Column('last_name', String))
    ... 
    >>> class Author(object):
    ...     pass
    ... 
    >>> mapper(Author, authors) #doctest: +ELLIPSIS
    <sqlalchemy.orm.mapper.Mapper object at ...>
    >>> books = Table('books', meta, 
    ...     Column('id', Integer, primary_key=True),
    ...     Column('title', String),
    ...     Column('author_id', Integer, ForeignKey('authors.id')))
    ... 
    >>> class Book(object):
    ...     pass
    ... 
    >>> mapper(Book, books) #doctest: +ELLIPSIS
    <sqlalchemy.orm.mapper.Mapper object at ...>
    >>> meta.create_all()

.. _sqlalchemy: http://www.sqlalchemy.org/
.. _Table: http://www.sqlalchemy.org/docs/tutorial.myt#tutorial_schemasql_table_creating
.. _mapped classes: http://www.sqlalchemy.org/docs/datamapping.myt
.. _sqlobject: http://sqlobject.org/
.. _SQLObject classes: http://sqlobject.org/SQLObject.html#declaring-the-class

Defining a Fixture
------------------

Define a fixture object like so::

    >>> from fixture import SQLAlchemyFixture
    >>> dbfixture = SQLAlchemyFixture(
    ...     env={'BookData': Book, 'AuthorData': Author},
    ...     session=session )
    ... 

For the available keyword arguments of respective LoadableFixture objects, see `SQLAlchemyFixture API`_ and `SQLObjectFixture API`_.

.. _SQLAlchemyFixture API: ../apidocs/fixture.loadable.sqlalcheny_loadable.SQLAlchemyFixture.html
.. _SQLObjectFixture API: ../apidocs/fixture.loadable.sqlobject_loadable.SQLObjectFixture.html

.. note::
    - Any keyword attribute of a LoadableFixture can be set later on as an 
      attribute of the instance.
    - LoadableFixture instances can safely be module-level objects
    - An ``env`` can be a dict or a module
    
Loading DataSet objects
-----------------------

As mentioned earlier, a DataSet shouldn't have to know how to store itself; the job of the Fixture object is to load and unload DataSet objects.  Let's consider the following DataSet objects (reusing the examples from earlier)::

    >>> from fixture import DataSet
    >>> class AuthorData(DataSet):
    ...     class frank_herbert:
    ...         first_name="Frank"
    ...         last_name="Herbert"
    >>> class BookData(DataSet):
    ...     class dune:
    ...         title = "Dune"
    ...         author_id = AuthorData.frank_herbert.ref('id')

As you recall, we passed a dictionary into the Fixture that associates the name ``BookData`` with the mapped class ``Book``.  Using this dict, a Fixture.Data instance now knows how to find the sqlalchemy mapped class when it comes across DataSets names.  Since we also gave it a ``session`` keyword, this will be used to save objects::
    
    >>> data = dbfixture.data(AuthorData, BookData)
    >>> data.setup() 
    >>> list(session.query(Book).select()) #doctest: +ELLIPSIS
    [<...Book object at ...>]
    >>> data.teardown()
    >>> list(session.query(Book).select())
    []

Discovering storable objects with Style
---------------------------------------

Loading objects using DataTestCase
----------------------------------

Loading objects using @dbfixture.with_data
------------------------------------------

Loading objects using the with statement
----------------------------------------

Defining a custom LoadableFixture
---------------------------------

You'll need to subclass `fixture.loadable.loadable:LoadableFixture`_ (more to come!)

.. _fixture.loadable.loadable:LoadableFixture: ../apidocs/fixture.loadable.loadable.LoadableFixture.html

"""

import sys
from fixture.base import Fixture
from fixture.util import ObjRegistry, _mklog
from fixture.style import OriginalStyle
from fixture.dataset import Ref, dataset_registry, DataRow
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
    
    def __init__(self, style=None, medium=None, dataclass=None):
        Fixture.__init__(self, loader=self, dataclass=dataclass)
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
            
        def save(self, row):
            """given a DataRow, save it somehow."""
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
    
    def attach_storage_medium(self):
        pass
    
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
        for key, row in ds:
            try:
                # resolve this row's referenced values :
                for k in row.columns():
                    v = getattr(row, k)
                    if isinstance(v, Ref.Value):
                        ref = v.ref
                        ref.dataset_obj = self.loaded[ref.dataset_class]
                        isref=True
                
                if not isinstance(row, DataRow):
                    row = row(ds)
                obj = ds.meta.storage_medium.save(row)
                ds.meta._stored_objects.store(key, obj)
                # save the instance in place of the class...
                ds._setdata(key, row)
                
            except Exception, e:
                etype, val, tb = sys.exc_info()
                raise LoadError(etype, val, ds, key=key, row=row), None, tb
        
        self.loaded.register(ds, level)
    
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
                        
        ds.meta.storage_medium = self.Medium(storable, ds)

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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
