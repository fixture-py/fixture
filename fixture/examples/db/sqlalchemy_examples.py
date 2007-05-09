
"""examples for using sqlalchemy fixtures.

Fixtures with SQLAlchemy and nose
---------------------------------

Create your tables and mappers.  Note that sqlalchemy extensions are used here 
only to make the assertions easier to read.::

    >>> from sqlalchemy import *
    >>> from sqlalchemy.ext.assignmapper import assign_mapper
    >>> from sqlalchemy.ext.sessioncontext import SessionContext
    
    >>> meta = BoundMetaData("sqlite:///:memory:")
    >>> session_context = SessionContext(
    ...     lambda: create_session(bind_to=meta.engine))
    ...
    >>> affiliates = Table('affiliates', meta,
    ...     Column('id', INT, primary_key=True),
    ...     Column('name', String),)
    ...     
    >>> class Affiliate(object): 
    ...     pass
    >>> m = assign_mapper(session_context, Affiliate, affiliates)
    
    >>> events = Table('events', meta,
    ...     Column('id', INT, primary_key=True),
    ...     Column('type', String),
    ...     Column('affiliate_id', INT,
    ...         ForeignKey('affiliates.id')),)
    ... 
    >>> class Event(object): 
    ...     pass
    >>> m = assign_mapper(session_context, Event, events, properties = {
    ...                 'affiliate': relation(Affiliate), }) 
    ...

Note that using mappers above is not necessary.  The fixture module supports 
interacting with assigned mappers, mapped classes, and tables.

Next you build the DataSet objects that you want to load.  Note that ID values 
are not specified in the row classes.  This is an optional feature where anytime 
the id attribute is referenced later on, it is found from the actual database 
object loaded, instead of the DataSet.  If you do specify an id attribute it 
will be recognized.  (Note that "id" names are configurable in 
Dataset.Meta.primary_key.)::

    >>> from fixture import DataSet
    >>> class affiliates_data(DataSet):
    ...     class joe:
    ...         name="Joe, The Affiliate"
    ... 
    >>> class events_data(DataSet):
    ...     class joes_click:
    ...         affiliate_id = affiliates_data.joe.ref('id')
    ...         type="click"
    ...     class joes_submit(joes_click):
    ...         type="submit"
    ...     class joes_activation(joes_click):
    ...         type="activation" 
    ...

Note how joes_submit inherits from joes_click.  Inheritance is a natural way to 
share common column values (in this case, all events belong to the same 
affiliate).

Next you need a module-level Fixture instance that knows how to load the above 
DataSet object(s).  We are also going to tell it to derive SQLAlchemy table 
names by looking in the global scope and chopping off "_data" from the DataSet 
class name (there are other ways to do this more or less explicitly).

We are going to pass it a session_context to create connections with, but again 
there are alternatives to this::

    >>> from fixture.style import TrimmedNameStyle    
    >>> from fixture import SQLAlchemyFixture
    >>> db = SQLAlchemyFixture( env=globals(), session_context=session_context,
    ...                         style=TrimmedNameStyle(suffix="_data"))
    ...

Now we are ready to write a test that uses the fixture.  Here is a test class 
using the provided TestCase mixin with python's builtin unittest module
    
    >>> from fixture import DataTestCase
    >>> import unittest
    >>> class TestWithEventData(DataTestCase, unittest.TestCase):
    ...     fixture = db
    ...     datasets = [events_data]
    ...     
    ...     def setUp(self):
    ...         meta.create_all()
    ...         super(TestWithEventData, self).setUp()
    ...     
    ...     def tearDown(self):
    ...         super(TestWithEventData, self).tearDown()
    ...         meta.drop_all()
    ...         # and do whatever else ...
    ...     
    ...     def test_event_something(self):
    ...         joe = Affiliate.get(self.data.affiliates_data.joe.id)
    ...         click = Event.get(self.data.events_data.joes_click.id)
    ...         assert click.affiliate is joe
    ...         assert click.type == self.data.events_data.joes_click.type
    ... 

Another way to write simpler tests is to use the builtin decorator, @with_data, designed for use with nose_ ::
 
    >>> def setup_data():
    ...     meta.create_all()
    ...
    >>> def teardown_data():
    ...     meta.drop_all()
    ...     # and do whatever else ...
    ...
    >>> @db.with_data(events_data, setup=setup_data, teardown=teardown_data)
    ... def test_event_something(data):
    ...     joe = Affiliate.get(data.affiliates_data.joe.id)
    ...     click = Event.get(data.events_data.joes_click.id)
    ...     assert click.affiliate is joe
    ...     assert click.type == data.events_data.joes_click.type
    ... 
    
The below is just code to run the tests (this is done automatically for 
you automatically by nose_ or unittest)::

    >>> import nose
    >>> from fixture.test import PrudentTestResult
    >>> result = PrudentTestResult()
    >>> loader = unittest.TestLoader()
    >>> suite = loader.loadTestsFromTestCase(TestWithEventData)
    >>> s = suite(result)
    >>> case = nose.case.FunctionTestCase(test_event_something)
    >>> case(result)
    >>> result.testsRun
    2
    >>> result.errors
    []
    >>> result.failures
    []

Here are some things to note.  @db.with_data() takes an arbitrary number of 
DataSet classes as an argument and passes an instance of Fixture.Data to the 
test function.  Because of the reference to affiliates_data, you don't have to 
specify that set since it will be discovered by reference.  Also note that there 
are other ways to load data.  Say, if you want to work with unittest.TestCase 
classes you could create the data instance you see above manually in a setUp() 
def, like data = db.data(events_data)

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

"""

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

Category, Product, Offer = None, None, None

if sqlalchemy:
    from sqlalchemy import *
    from sqlalchemy.orm.mapper import global_extensions
    from sqlalchemy.ext.sessioncontext import SessionContext
    from sqlalchemy.ext.assignmapper import assign_mapper
    
    categories = Table("fixture_sqlalchemy_category",
        Column("id", INT, primary_key=True),
        Column("name", String )
    )
    class Category(object):
        pass
    
    products = Table("fixture_sqlalchemy_product",
        Column("id", INT, primary_key=True),
        Column("name", String ),
        Column("category_id", INT, 
                ForeignKey("fixture_sqlalchemy_category.id")),
    )
    class Product(object):
        pass
    
    offers = Table("fixture_sqlalchemy_offer",
        Column("id", INT, primary_key=True),
        Column("name", String ),
        Column("category_id", INT, 
                ForeignKey("fixture_sqlalchemy_category.id")),
        Column("product_id", INT, 
                ForeignKey("fixture_sqlalchemy_product.id")),
    )
    class Offer(object):
        pass
        
    dynamic_meta = DynamicMetaData()
    session = create_session(engine)
    authors = Table('authors', dynamic_meta,
        Column('id', Integer, primary_key=True),
        Column('first_name', String),
        Column('last_name', String))

    class Author(object):
        pass

    mapper(Author, authors)
    books = Table('books', dynamic_meta, 
        Column('id', Integer, primary_key=True),
        Column('title', String),
        Column('author_id', Integer, ForeignKey('authors.id')))

    class Book(object):
        pass

    mapper(Book, books)

def setup_db(meta, session_context, **kw):
    assert sqlalchemy
    
    def assign_and_create(obj, table, **localkw):
        table.tometadata(meta)
        sendkw = dict([(k,v) for k,v in localkw.items()])
        sendkw.update(kw)
        assign_mapper(session_context, obj, table, **sendkw)
        checkfirst=False
        import sys
        table.create(meta.engine, checkfirst=checkfirst)
    
    assign_and_create(Category, categories)
    assign_and_create(Product, products)
    assign_and_create(Offer, offers)

def teardown_db(meta, session_context):
    import sqlalchemy
    engine = session_context.current.bind_to
    meta.drop_all()
    if hasattr(engine, 'engine'):
        # then it is a connectable...
        engine = engine.engine
    engine.dispose()
    
    sqlalchemy.orm.clear_mappers()
    session_context.current.clear()
    session_context.current = None
    