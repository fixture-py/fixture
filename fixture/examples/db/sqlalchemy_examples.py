
"""examples for using sqlalchemy fixtures.

SequencedSet Fixtures with SQLAlchemy and nose
----------------------------------------------

Create your tables::

    >>> from sqlalchemy import *
    >>> from sqlalchemy.ext.sessioncontext import SessionContext
    >>> from sqlalchemy.ext.assignmapper import assign_mapper
     
    >>> meta = BoundMetaData("sqlite:///:memory:")
    >>> session_context = SessionContext(
    ...     lambda: create_session(bind_to=meta.engine))
    ... 
    >>> affiliates = Table('affiliates', meta,
    ...     Column('id', INT, primary_key=True),
    ...     Column('name', String),)
    ...     
    >>> class Affiliate(object): pass
    >>> m = assign_mapper(session_context, Affiliate, affiliates) 
    >>> events = Table('events', meta,
    ...     Column('id', INT, primary_key=True),
    ...     Column('type', String),
    ...     Column('affiliate_id', INT,
    ...         ForeignKey('affiliates.id')),)
    ...         
    >>> class Event(object): pass
    >>> m = assign_mapper(session_context, Event, events, properties = {
    ...                                 'affiliate': relation(Affiliate), }) 

Note that using mappers above is not necessary.  The fixture module also 
supports interacting with mapper classes, however.

Next you build the DataSet objects that you want to load, in this case they 
inherit from SequencedSet, an optional DataSet enhancement that simulates 
auto-incrementing IDs.  The ID values can be overridden for any row and the 
column name is configurable, but defaults to 'id'::

    >>> from fixture import SequencedSet
    >>> class affiliates_data(SequencedSet):
    ...     class joe:
    ...         name="Joe, The Affiliate"
    ... 
    >>> class events_data(SequencedSet):
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

Now we are ready to write a test that uses the fixtures.  The following is just one way you could write a test function runnable by nose_ ::
 
    >>> def setup_data():
    ...     meta.create_all()
    ...
    >>> def teardown_data():
    ...     meta.drop_all()
    ...     clear_mappers()
    ...     # and do whatever else ...
    ...
    >>> @db.with_data(events_data, setup=setup_data, teardown=teardown_data)
    ... def test_event_something(data):
    ...     joe = Affiliate.get(data.affiliates_data.joe.id)
    ...     click = Event.get(data.events_data.joes_click.id)
    ...     assert click.affiliate is joe
    ...     assert click.type == data.events_data.joes_click.type
    ... 
    
The rest will be done for you automatically by nose_::

    >>> import nose, unittest
    >>> result = unittest.TestResult()
    >>> case = nose.case.FunctionTestCase(test_event_something)
    >>> case(result)
    >>> result.testsRun
    1
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
        Column("product_id", INT, ForeignKey("fixture_sqlalchemy_product.id")),
    )
    class Offer(object):
        pass

def setup_db(meta, session_context, **kw):
    assert sqlalchemy
    
    def assign_and_create(obj, table, **localkw):
        table.tometadata(meta)
        sendkw = dict([(k,v) for k,v in localkw.items()])
        sendkw.update(kw)
        assign_mapper(session_context, obj, table, **sendkw)
        checkfirst=False
        table.create(meta.engine, checkfirst=checkfirst)
        # if checkfirst:
        #     meta.engine.execute(table.delete(cascade=True))
    
    
    assign_and_create(Category, categories)
    assign_and_create(Product, products)
    assign_and_create(Offer, offers)
    
    # session = session_context.current
    # session.flush()
    # session.clear()

def teardown_db(meta, session_context):
    import sqlalchemy
    meta.drop_all()
    
    # session = session_context.current
    # session.flush()
    
    sqlalchemy.orm.clear_mappers()
    
    