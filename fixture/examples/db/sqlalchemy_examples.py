
"""examples for using sqlalchemy fixtures.

Fixtures with SQLAlchemy and nose
---------------------------------

Create your tables and mappers.  Note that if you have mappers attached to sessions, those mappers *must* be created with the option ``save_on_init=False``.  This is allows fixture to use a privately-scoped session when performing setup/teardown and thus work independently from the application under test.::

    >>> from sqlalchemy import *
    >>> from sqlalchemy.orm import *
    >>> meta = MetaData("sqlite:///:memory:")
    >>> Session = scoped_session(sessionmaker(bind=meta.bind, autoflush=False, transactional=True))
    >>> affiliates = Table('affiliates', meta,
    ...     Column('id', INT, primary_key=True),
    ...     Column('name', String(60)),)
    ...     
    >>> class Affiliate(object): 
    ...     pass
    >>> m = Session.mapper(Affiliate, affiliates, save_on_init=False)
    
    >>> events = Table('events', meta,
    ...     Column('id', INT, primary_key=True),
    ...     Column('type', String(30)),
    ...     Column('affiliate_id', INT,
    ...         ForeignKey('affiliates.id')),)
    ... 
    >>> class Event(object): 
    ...     pass
    >>> m = Session.mapper(Event, events, properties = {
    ...         'affiliate': relation(Affiliate), 
    ...     }, save_on_init=False) 
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

We are going to pass it an engine to use and a custom type that can be used to find mapped objects::

    >>> from fixture import SQLAlchemyFixture, TrimmedNameStyle
    >>> db = SQLAlchemyFixture( env=globals(), engine=meta.bind, style=TrimmedNameStyle(suffix="_data"))
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
    ...     def test_events(self):
    ...         joe = Affiliate.query().filter_by(id=self.data.affiliates_data.joe.id).one()
    ...         click = Event.query().filter_by(id=self.data.events_data.joes_click.id).one()
    ...         assert click.affiliate is joe
    ...         assert click.type == self.data.events_data.joes_click.type
    ... 
    >>> from fixture.test import PrudentTestResult
    >>> result = PrudentTestResult()
    >>> case = TestWithEventData('test_events')
    >>> case(result)
    >>> result
    <fixture.test.PrudentTestResult run=1 errors=0 failures=0>

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
    ...     joe = Affiliate.query().filter_by(id=data.affiliates_data.joe.id).all()[0]
    ...     click = Event.query().filter_by(id=data.events_data.joes_click.id).all()[0]
    ...     assert click.affiliate is joe
    ...     assert click.type == data.events_data.joes_click.type
    ... 
    >>> from nose.case import FunctionTestCase
    >>> from fixture.test import PrudentTestResult
    >>> result = PrudentTestResult()
    >>> case = FunctionTestCase(test_event_something)
    >>> case(result)
    >>> result
    <fixture.test.PrudentTestResult run=1 errors=0 failures=0>

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
    from sqlalchemy.orm import *
    metadata = MetaData()
    
    categories = Table("fixture_sqlalchemy_category",
        metadata,
        Column("id", INT, primary_key=True),
        Column("name", String(100) )
    )
    class Category(object):
        pass
    
    products = Table("fixture_sqlalchemy_product",
        metadata,
        Column("id", INT, primary_key=True),
        Column("name", String(100) ),
        Column("category_id", INT, 
                ForeignKey("fixture_sqlalchemy_category.id")),
    )
    class Product(object):
        pass
    
    offers = Table("fixture_sqlalchemy_offer",
        metadata,
        Column("id", INT, primary_key=True),
        Column("name", String(100) ),
        Column("category_id", INT, 
                ForeignKey("fixture_sqlalchemy_category.id")),
        Column("product_id", INT, 
                ForeignKey("fixture_sqlalchemy_product.id")),
    )
    class Offer(object):
        pass
        
    authors = Table('authors', metadata,
        Column('id', Integer, primary_key=True),
        Column('first_name', String(100)),
        Column('last_name', String(100)))

    class Author(object):
        pass

    books = Table('books', metadata, 
        Column('id', Integer, primary_key=True),
        Column('title', String(100)),
        Column('author_id', Integer, ForeignKey('authors.id')))

    class Book(object):
        pass

def connect(dsn):
    metadata.bind = create_engine(dsn)

def setup_mappers():
    mapper(Category, categories)
    mapper(Product, products, properties={
        'category': relation(Category),
    })
    mapper(Offer, offers, properties={
        'category': relation(Category, backref='products'),
        'product': relation(Product)
    })
    mapper(Author, authors)
    mapper(Book, books, properties={
        'author': relation(Author)
    })

if __name__ == '__main__':
    import doctest
    doctest.testmod()