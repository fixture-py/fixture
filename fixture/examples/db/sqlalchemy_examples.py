
"""examples for using sqlalchemy fixtures.

    >>> from sqlalchemy import *
    >>> from sqlalchemy.ext.sessioncontext import SessionContext
    >>> from sqlalchemy.ext.assignmapper import assign_mapper
     
    >>> meta = BoundMetaData("sqlite:///:memory:")
    >>> session_context = SessionContext(
    ...     lambda: create_session(bind_to=meta.engine))
    ... 
    >>> # your table definitions...
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
    >>> m = assign_mapper(session_context, Event, events) 
    >>> from fixture import SequencedSet, SQLAlchemyFixture
    >>> from fixture.style import TrimmedNameStyle
     
    >>> # some datasets you want to load in a test...
    >>> class affiliates_data(SequencedSet):
    ...     class joe:
    ...         name="Joe, The Affiliate"
    ... 
    >>> class events_data(SequencedSet):
    ...     class joes_click:
    ...         affiliate_id = affiliates_data.joe.ref('id'),
    ...         type="click"
    ...     class joes_submit(joes_click):
    ...         type="submit"
    ...     class joes_activation(joes_click):
    ...         type="activation" 
    >>> db = SQLAlchemyFixture( env=globals(), session_context=session_context,
    ...                         style=TrimmedNameStyle(suffix="_data"))
    ...         
    >>> def setup_data():
    ...     meta.create_all()
    ...
    >>> def teardown_data():
    ...     meta.drop_all()
    ...     clear_mappers()
    ...     # and clear mappers et cetera ...
    ... 
    >>> @db.with_data(events_data, setup=setup_data, teardown=teardown_data)
    ... def test_event_something(data):
    ...     joe = Affiliate.get(data.affiliates_data.joe.id)
    ...     click = Events.get(data.events_data.joes_click.id)
    ...     assert click.affiliate is joe
    ...     assert click.type == data.events_data.joes_click.type
    ... 
    >>> import nose, unittest
    >>> case = nose.case.FunctionTestCase(test_event_something)
    >>> case(unittest.TestResult())

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
    
    