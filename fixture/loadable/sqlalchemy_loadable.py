
"""Components for loading and unloading data using `SQLAlchemy`_.

See :ref:`Using LoadableFixture<using-loadable-fixture>` for examples.

.. _SQLAlchemy: http://www.sqlalchemy.org/

"""

import sys
from fixture.loadable import DBLoadableFixture
from fixture.exc import UninitializedError
import logging

log = logging.getLogger('fixture.loadable.sqlalchemy_loadable')

try:
    from sqlalchemy.orm import sessionmaker, scoped_session
except ImportError:
    Session = None
    sa_major = None
else:
    import sqlalchemy
    sa_major = float(sqlalchemy.__version__[:3]) # i.e. 0.4 or 0.5
    if sa_major < 0.5:
        Session = scoped_session(sessionmaker(autoflush=False, transactional=True), scopefunc=lambda:__name__)
    else:
        Session = scoped_session(sessionmaker(autoflush=False, autocommit=False), scopefunc=lambda:__name__)

def negotiated_medium(obj, dataset):
    if is_table(obj):
        return TableMedium(obj, dataset)
    elif is_assigned_mapper(obj):
        return MappedClassMedium(obj, dataset)
    elif is_mapped_class(obj):
        return MappedClassMedium(obj, dataset)
    else:
        raise NotImplementedError("object %s is not supported by %s" % (
                                                    obj, SQLAlchemyFixture))

class SQLAlchemyFixture(DBLoadableFixture):
    """
    A fixture that knows how to load DataSet objects into `SQLAlchemy`_ objects.
    
    >>> from fixture import SQLAlchemyFixture
    
    The recommended way to deal with connections is to either pass in your own engine object 
    or let `implicit binding`_ govern how connections are made.  This is because 
    ``SQLAlchemyFixture`` will use an internally scoped session to avoid conflicts 
    with that of the Application Under Test.  If you need to bypass this behavior then 
    pass in your own session or scoped_session.
    
    For examples of usage see :ref:`Using LoadableFixture <using-loadable-fixture>`
    
    .. _implicit binding: http://www.sqlalchemy.org/docs/04/dbengine.html#dbengine_implicit
    
    Keyword Arguments:
    
    ``style``
        A :class:`Style <fixture.style.Style>` object to translate names with
    
    ``env``
        A dict or module that contains either mapped classes or Table objects,
        or both.  This will be searched when :class:`Style <fixture.style.Style>` 
        translates DataSet names into
        storage media.  See :meth:`EnvLoadableFixture.attach_storage_medium <fixture.loadable.loadable.EnvLoadableFixture.attach_storage_medium>` for details on 
        how ``env`` works.
    
    ``engine``
        A specific connectable/engine object to use when one is not bound.  
        engine.connect() will be called.
    
    ``session``
        A session from ``sqlalchemy.create_session()``.  See `Contextual/Thread-local Sessions`_
        for more info.  This will override the 
        ScopedSession and SessionContext approaches.  Only declare a session if you have to.  
        The preferred way is to let fixture use its own session in a private scope.
    
    .. _Contextual/Thread-local Sessions: http://www.sqlalchemy.org/docs/04/session.html#unitofwork_contextual
    
    ``scoped_session``
        A class-like ``Session`` object created by ``scoped_session(sessionmaker())``.  
        Only declare a custom Session if you have to.  The preferred way 
        is to let fixture use its own Session which defines a private scope to 
        avoid conflicts with that of the Application Under Test.
    
    ``connection``
        A specific connection / engine to use when one is not bound.
    
    ``dataclass``
        :class:`SuperSet <fixture.dataset.SuperSet>` class to represent loaded data with
    
    ``medium``
        A custom :class:`StorageMediumAdapter <fixture.loadable.loadable.StorageMediumAdapter>` 
        to instantiate when storing a DataSet.
        By default, a medium adapter will be negotiated based on the type of 
        SQLAlchemy object so you should only set this if you know what you 
        doing.
    
    """
    Medium = staticmethod(negotiated_medium)
    
    def __init__(self, engine=None, connection=None, session=None, scoped_session=None, **kw):
        # ensure import error by simulating what would happen in the global module :
        from sqlalchemy.orm import sessionmaker, scoped_session as sa_scoped_session 
        
        DBLoadableFixture.__init__(self, **kw)
        self.engine = engine
        self.connection = connection
        self.session = session
        if scoped_session is None:
            scoped_session = Session
        self.Session = scoped_session
    
    def begin(self, unloading=False):
        """Begin loading data
        
        - creates and stores a connection with engine.connect() if an engine was passed
          
          - binds the connection or engine to fixture's internal session
          
        - uses an unbound internal session if no engine or connection was passed in
        """
        if not unloading:
            # ...then we are loading, so let's *lazily* 
            # clean up after a previous setup/teardown
            Session.remove()
        if self.connection is None and self.engine is None:
            if self.session:
                self.engine = self.session.bind # might be None
        
        if self.engine is not None and self.connection is None:
            self.connection = self.engine.connect()
        
        if self.session is None:
            if self.connection:
                self.session = self.Session(bind=self.connection)
            else:
                self.session = self.Session(bind=None)
            
        DBLoadableFixture.begin(self, unloading=unloading)
    
    def commit(self):
        """Commit the load transaction and flush the session
        """
        if self.connection:
            # note that when not using a connection, calling session.commit() 
            # as the inheirted code does will automatically flush the session
            self.session.flush()
        
        log.debug("transaction.commit() <- %s", self.transaction)
        DBLoadableFixture.commit(self)
    
    def create_transaction(self):
        """Create a session transaction or a connection transaction
        
        - if a custom connection was used, calls connection.begin
        - otherwise calls session.begin()
        
        """
        if self.connection is not None:
            log.debug("connection.begin()")
            transaction = self.connection.begin()
        else:
            transaction = self.session.begin()
        log.debug("create_transaction() <- %s", transaction)
        return transaction
    
    def dispose(self):
        """Dispose of this fixture instance entirely
        
        Closes all connection, session, and transaction objects and calls engine.dispose()
        
        After calling fixture.dispose() you cannot use the fixture instance.  
        Instead you have to create a new instance like::
        
            fixture = SQLAlchemyFixture(...)
        
        """
        from fixture.dataset import dataset_registry
        dataset_registry.clear()
        if self.connection:
            self.connection.close()
        if self.session:
            self.session.close()
        if self.transaction:
            self.transaction.close()
        if self.engine:
            self.engine.dispose()
    
    def rollback(self):
        """Rollback load transaction"""
        DBLoadableFixture.rollback(self)

## this was used in an if branch of clear() ... but I think this is no longer necessary with scoped sessions
## does it need to exist for 0.4 ?  not sure
# def object_was_deleted(session, obj):
#     # hopefully there is a more future proof way to do this...
#     from sqlalchemy.orm.mapper import object_mapper
#     for c in [obj] + list(object_mapper(obj).cascade_iterator(
#                                                     'delete', obj)):
#         if c in session.deleted:
#             return True
#         elif not session.uow._is_valid(c):
#             # it must have been deleted elsewhere.  is there any other 
#             # reason for this scenario?
#             return True
#     return False

class MappedClassMedium(DBLoadableFixture.StorageMediumAdapter):
    """
    Adapter for `SQLAlchemy`_ mapped classes.
    
    For example, in ``mapper(TheClass, the_table)`` ``TheClass`` is a mapped class.
    If using `Elixir`_ then any class descending from ``elixir.Entity`` is treated like a mapped class.
    
    .. _Elixir: http://elixir.ematia.de/
    
    """
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        
    def clear(self, obj):
        """Delete this object from the session"""
        self.session.delete(obj)
    
    def visit_loader(self, loader):
        """Visits the :class:`SQLAlchemyFixture` loader and stores a reference to its session"""
        self.session = loader.session
        
    def save(self, row, column_vals):
        """Save a new object to the session if it doesn't already exist in the session."""
        obj = self.medium()
        for c, val in column_vals:
            setattr(obj, c, val)
        if obj not in self.session.new:
            if hasattr(self.session, 'add'):
                # sqlalchemy 0.5.2+
                self.session.add(obj)
            else:
                self.session.save(obj)
        return obj


class LoadedTableRow(object):
    def __init__(self, table, inserted_key, conn):
        self.table = table
        self.conn = conn
        self.inserted_key = [k for k in inserted_key]
        self.row = None
    
    def __getattr__(self, col):
        if not self.row:
            if len(self.inserted_key) > 1:
                raise NotImplementedError(
                    "%s does not support making a select statement with a "
                    "composite key, %s.  This is probably fixable" % (
                                        self.__class__.__name__, 
                                        self.table.primary_key))
            
            first_pk = [k for k in self.table.primary_key][0]
            id = getattr(self.table.c, first_pk.key)
            stmt = self.table.select(id==self.inserted_key[0])
            if self.conn:
                c = self.conn.execute(stmt)
            else:
                c = stmt.execute()
            self.row = c.fetchone()
        return getattr(self.row, col)
             
class TableMedium(DBLoadableFixture.StorageMediumAdapter):
    """
    Adapter for `SQLAlchemy Table objects`_
    
    If no connection or engine is configured in the :class:`SQLAlchemyFixture` 
    then statements will be executed directly on the Table object itself which adheres 
    to `implicit connection rules`_.  Otherwise, 
    the respective connection or engine will be used to execute statements.
    
    .. _SQLAlchemy Table objects: http://www.sqlalchemy.org/docs/04/ormtutorial.html#datamapping_tables
    .. _implicit connection rules: http://www.sqlalchemy.org/docs/04/dbengine.html#dbengine_implicit
    
    """
            
    def __init__(self, *a,**kw):
        DBLoadableFixture.StorageMediumAdapter.__init__(self, *a,**kw)
        self.conn = None
        
    def clear(self, obj):
        """Constructs a delete statement per each primary key and 
        executes it either explicitly or implicitly
        """
        i=0
        for k in obj.table.primary_key:
            id = getattr(obj.table.c, k.key)
            stmt = obj.table.delete(id==obj.inserted_key[i])
            if self.conn:
                c = self.conn.execute(stmt)
            else:
                c = stmt.execute()
            i+=1
    
    def visit_loader(self, loader):
        """Visits the :class:`SQLAlchemyFixture` loader and stores a reference 
        to its connection if there is one.
        """
        if loader.connection:
            self.conn = loader.connection
        else:
            self.conn = None
        
    def save(self, row, column_vals):
        """Constructs an insert statement with the given values and 
        executes it either explicitly or implicitly
        """
        from sqlalchemy.schema import Table
        if not isinstance(self.medium, Table):
            raise ValueError(
                "medium %s must be a Table instance" % self.medium)
                
        stmt = self.medium.insert()
        params = dict(list(column_vals))
        if self.conn:
            c = self.conn.execute(stmt, params)
        else:
            c = stmt.execute(params)

        # In SQLAlchemy 0.8 this changed to a property with another name
        if hasattr(c, "primary_key"):
            primary_key = c.primary_key
        else:
            primary_key = c.last_inserted_ids()

        if primary_key is None:
            raise NotImplementedError(
                    "what can we do with a None primary key?")
        table_keys = [k for k in self.medium.primary_key]
        inserted_keys = [k for k in primary_key]
        if len(inserted_keys) != len(table_keys):
            raise ValueError(
                "expected primary_key %s, got %s (using table %s)" % (
                                table_keys, inserted_keys, self.medium))
        
        return LoadedTableRow(self.medium, primary_key, self.conn)

def is_assigned_mapper(obj):
    import sqlalchemy
    if sa_major <= 0.3:
        from sqlalchemy.orm.mapper import Mapper
        def is_assigned(obj):
            return hasattr(obj, 'mapper') and isinstance(obj.mapper, Mapper)
    else:
        if sa_major < 0.5:
            from sqlalchemy import exceptions as sqlalchemy_exc
        else:
            from sqlalchemy import exc as sqlalchemy_exc

        # 0.4 and 0.5 +
        from sqlalchemy.orm.mapper import class_mapper
        def is_assigned(obj):
            try:
                cm = class_mapper(obj)
            except sqlalchemy_exc.InvalidRequestError:
                return False
            return True
            
    return is_assigned(obj)

def is_mapped_class(obj):
    # hrrmmm, really?
    if sa_major < 0.5:
        from sqlalchemy import util
        return hasattr(obj, 'c') and isinstance(obj.c, util.OrderedProperties)
    else:
        # 0.5 :
        return hasattr(obj, '_sa_class_manager')

def is_table(obj):
    from sqlalchemy.schema import Table
    return isinstance(obj, Table)
