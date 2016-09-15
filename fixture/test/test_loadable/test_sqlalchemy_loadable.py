import unittest

from six import print_

from fixture.examples.db.sqlalchemy_examples import *
from fixture.loadable.sqlalchemy_loadable import *
from fixture.test import conf, env_supports
from fixture.test.test_loadable import *


def get_transactional_session():
    if sa_major < 0.5:
        session = scoped_session(
            sessionmaker(
                autoflush=False,
                transactional=True,
                ),
            scopefunc=lambda:__name__
            )
        return session
    else:
        session = scoped_session(
            sessionmaker(
                autoflush=True,
                autocommit=False,
                ),
            scopefunc=lambda:__name__
            )
        return session

def clear_session(session):
    """ This method has a different name from version 0.5 """
    if sa_major < 0.5:
        session.clear()
    else:
        session.expunge_all()

def save_session(session, object):
    """ This method has a different name from version 0.5 """
    if sa_major < 0.5:
        session.save(object)
    else:
        session.add(object)

def setup():
    if not env_supports.sqlalchemy: raise SkipTest

def teardown():
    pass

@raises(UninitializedError)
def test_cannot_teardown_unloaded_fixture():
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
            
    engine = create_engine(conf.LITE_DSN)
    metadata.bind = engine
    
    db = SQLAlchemyFixture(
        env=globals(),
        engine=metadata.bind
    )
    data = db.data(CategoryData)
    data.teardown()

@attr(unit=1)
def test_negotiated_medium():
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
            
    engine = create_engine(conf.LITE_DSN)
    metadata.bind = engine
    metadata.create_all()
    
    eq_(type(negotiated_medium(categories, CategoryData)), TableMedium)
    eq_(is_table(categories), True)
    
    clear_mappers()
    mapper(Category, categories)
    
    eq_(type(negotiated_medium(Category, CategoryData)), MappedClassMedium)
    eq_(is_mapped_class(Category), True)
    # hmmm
    # eq_(is_assigned_mapper(Category), False)
    
    clear_mappers()
    ScopedSession = scoped_session(get_transactional_session())
    ScopedSession.mapper(Category, categories)
    
    eq_(type(negotiated_medium(Category, CategoryData)), MappedClassMedium)
    eq_(is_mapped_class(Category), True)
    eq_(is_assigned_mapper(Category), True)
    
@attr(unit=1)
def test_negotiated_medium_05():            
    if sa_major < 0.5:
        raise SkipTest("Requires SQLAlchemy >= 0.5")
        
    class FooData(DataSet):
        class foo:
            name = 'foozilator'
            
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    engine = create_engine(conf.LITE_DSN)

    class DeclarativeFoo(Base):
        __tablename__ = 'fixture_declarative_foo'
        id = Column(Integer, primary_key=True)
        name = Column(String)
    
    DeclarativeFoo.metadata.bind = engine
    DeclarativeFoo.__table__.create()
    try:
        eq_(type(negotiated_medium(DeclarativeFoo, FooData)), MappedClassMedium)
    finally:
        DeclarativeFoo.__table__.drop()

class TestSetupTeardown(unittest.TestCase):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        engine = create_engine(conf.LITE_DSN)
        metadata.bind = engine
        metadata.create_all()
        Session = get_transactional_session()
        self.session = Session()
        self.fixture = SQLAlchemyFixture(
            env={'CategoryData':Category},
            engine=metadata.bind
        )
        
        clear_mappers()
        mapper(Category, categories)
    
    def tearDown(self):
        metadata.drop_all()
        self.session.close()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        eq_(self.session.query(Category).all(), [])
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        clear_session(self.session)
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        clear_session(self.session)
        eq_(list(self.session.query(Category)), [])


class TestImplicitSABinding(unittest.TestCase):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        engine = create_engine(conf.LITE_DSN)
        metadata.bind = engine
        # metadata.bind.echo = True
        metadata.create_all()
        
        Session = get_transactional_session()
        self.session = Session()
        
        # note the lack of explicit binding :
        self.fixture = SQLAlchemyFixture(
            env={'CategoryData':Category},
        )
        
        clear_mappers()
        # since categories is assigned to metadata, SA should handle binding for us
        mapper(Category, categories)
    
    def tearDown(self):
        # metadata.bind.echo = False
        metadata.drop_all()
        self.session.close()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        eq_(self.session.query(Category).all(), [])
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        
        clear_session(self.session)
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        clear_session(self.session)
        eq_(list(self.session.query(Category)), [])
        
class CategoryData(DataSet):
    class cars:
        name = 'cars'
    class free_stuff:
        name = 'get free stuff'

class ProductData(DataSet):
    class truck:
        name = 'truck'
        category = CategoryData.cars

class OfferData(DataSet):
    class free_truck:
        name = "it's a free truck"
        product = ProductData.truck
        category = CategoryData.free_stuff
    class free_spaceship(free_truck):
        id = 99
        name = "it's a free spaceship"
    class free_tv(free_spaceship):
        name = "it's a free TV"
        
class TestCascadingReferences(unittest.TestCase):
    CategoryData = CategoryData
    ProductData = ProductData
    OfferData = OfferData
    
    def setUp(self):
        if not conf.HEAVY_DSN:
            raise SkipTest("conf.HEAVY_DSN not defined")
        engine = create_engine(conf.HEAVY_DSN)
        metadata.bind = engine
        metadata.create_all()
        Session = get_transactional_session()
        self.session = Session()
        
        self.fixture = SQLAlchemyFixture(
            env=globals(),
            engine=metadata.bind,
            style=NamedDataStyle(),
        )
        
        clear_mappers()
        
        mapper(Category, categories)
        mapper(Product, products, properties={
            'category': relation(Category, backref='products')
        })
        mapper(Offer, offers, properties={
            'product': relation(Product, backref='offers'),
            'category': relation(Category, backref='offers')
        })
    
    def tearDown(self):
        metadata.drop_all()
        self.session.close()
        clear_mappers()
        # self.conn.close()
        metadata.bind.dispose()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        eq_(self.session.query(Category).all(), [])
        eq_(self.session.query(Product).all(), [])
        eq_(self.session.query(Offer).all(), [])
        
        data = self.fixture.data(self.OfferData)
        data.setup()
        clear_session(self.session)
        
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        prods = self.session.query(Product).order_by('name').all()
        eq_(prods[0].name, 'truck')
        eq_(prods[0].category, cats[0])
        
        off = self.session.query(Offer).order_by('name').all()
        eq_(off[0].name, "it's a free TV")
        eq_(off[0].product, prods[0])
        eq_(off[0].category, cats[1])
        
        eq_(off[1].name, "it's a free spaceship")
        eq_(off[1].product, prods[0])
        eq_(off[1].category, cats[1])
        
        eq_(off[2].name, "it's a free truck")
        eq_(off[2].product, prods[0])
        eq_(off[2].category, cats[1])
        
        data.teardown()
        clear_session(self.session)
        
        eq_(self.session.query(Category).all(), [])
        eq_(self.session.query(Product).all(), [])
        eq_(self.session.query(Offer).all(), [])

class TestCollidingSessions(unittest.TestCase):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        self.engine = create_engine(conf.LITE_DSN)
        # self.conn = self.engine.connect()
        metadata.bind = self.engine
        # metadata.bind.echo = True
        metadata.create_all()
        # metadata.bind.echo = False
        self.ScopedSession = scoped_session(get_transactional_session())
        self.session = self.ScopedSession()
        self.fixture = SQLAlchemyFixture(
            env={'CategoryData':Category},
            engine=metadata.bind
        )
        
        clear_mappers()
        mapper(Category, categories)
    
    def tearDown(self):
        metadata.drop_all()
        self.session.close()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        eq_(self.session.query(Category).all(), [])
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        clear_session(self.session)
        
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        # simulate the application running into some kind of error:
        new_cat = Category()
        new_cat.name = "doomed to non-existance"
        save_session(self.session, new_cat)
        self.session.rollback()
        self.ScopedSession.remove()
        
        data.teardown()
        clear_session(self.session)
        
        print_([(c.id, c.name) for c in self.session.query(Category).all()])
        eq_(list(self.session.query(Category)), [])

class TestScopedSessions(unittest.TestCase):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        self.engine = create_engine(conf.LITE_DSN)
        metadata.bind = self.engine
        metadata.create_all()
        ScopedSession = scoped_session(get_transactional_session())
        self.session = ScopedSession()
        self.fixture = SQLAlchemyFixture(
            env={'CategoryData':Category},
            engine=metadata.bind
        )
        
        clear_mappers()
        mapper(Category, categories)
    
    def tearDown(self):
        metadata.drop_all()
        self.session.close()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        eq_(self.session.query(Category).all(), [])
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        clear_session(self.session)
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        clear_session(self.session)
        eq_(list(self.session.query(Category)), [])

class TestElixir(unittest.TestCase):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        if not env_supports.elixir:
            raise SkipTest("elixir module not found")
        import elixir
        
        self.engine = create_engine(conf.LITE_DSN)
        metadata.bind = self.engine
        metadata.create_all()
        
        class CategoryEntity(elixir.Entity):
            elixir.using_options(tablename=str(categories))
            # save_on_init IS VERY IMPORTANT
            elixir.using_mapper_options(save_on_init=False)
            
        self.CategoryEntity = CategoryEntity
        
        self.fixture = SQLAlchemyFixture(
            env={'CategoryData':CategoryEntity},
            engine=metadata.bind
        )
        
        elixir.metadata.bind = self.engine
        elixir.setup_all()
    
    def tearDown(self):
        metadata.drop_all()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        try:
            from elixir import session as elixir_session
        except ImportError:
            from elixir import objectstore as elixir_session
        
        eq_(len(elixir_session.query(self.CategoryEntity).all()), 0)
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        
        eq_(len(elixir_session.query(self.CategoryEntity).all()), 2)
        
        data.teardown()
        eq_(elixir_session.query(self.CategoryEntity).all(), [])

class TestTableObjects(unittest.TestCase):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        self.engine = create_engine(conf.LITE_DSN)
        metadata.bind = self.engine
        metadata.create_all()
        Session = get_transactional_session()
        self.session = Session()
        self.fixture = SQLAlchemyFixture(
            # maps to a table object :
            env={'CategoryData':categories},
            engine=metadata.bind
        )
        
        clear_mappers()
        mapper(Category, categories)
    
    def tearDown(self):
        metadata.drop_all()
        self.session.close()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        eq_(self.session.query(Category).all(), [])
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        clear_session(self.session)
        
        cats = self.session.execute(categories.select()).fetchall()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        clear_session(self.session)
        eq_(self.session.execute(categories.select()).fetchall(), [])

class TestTableObjectsExplicitConn(object):
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        if not conf.HEAVY_DSN:
            raise SkipTest("conf.HEAVY_DSN not defined")
    
        self.litemeta = MetaData(bind=conf.LITE_DSN)
        LiteSession = sessionmaker(bind=self.litemeta.bind)
        self.litesession = LiteSession()
        
        heavymeta = MetaData(bind=create_engine(conf.HEAVY_DSN))
        HeavySession = sessionmaker(bind=heavymeta.bind)
        self.heavysession = HeavySession()
    
        # this creates the default bind:
        metadata.bind = heavymeta.bind
        metadata.create_all()
    
        # this creates the table in mem but does not bind 
        # the connection to the table:
        categories.create(bind=self.litemeta.bind)
        
        clear_mappers()
        mapper(Category, categories)
    
    def tearDown(self):
        metadata.drop_all()
    
    def test_with_engine_connection(self):
        fixture = SQLAlchemyFixture(
            # maps to a table object :
            env={'CategoryData':categories},
            # this should overwrite the default bind:
            engine = self.litemeta.bind
        )
        data = fixture.data(CategoryData)
        data.setup()
        
        rs = self.heavysession.query(Category).all()
        assert rs==[], "unexpected records in HEAVY_DSN db: %s" % rs 
        
        rs = self.litesession.query(Category).all()
        eq_(len(rs), 2)
        
        data.teardown()
        
        rs = self.litesession.query(Category).all()
        eq_(len(rs), 0)


def test_fixture_can_be_disposed():
    if sa_major < 0.5:
        from sqlalchemy.exceptions import InvalidRequestError
    else:
        from sqlalchemy.exc import InvalidRequestError
    engine = create_engine(conf.LITE_DSN)
    metadata.bind = engine
    metadata.create_all()
    Session = get_transactional_session()
    session = Session()
    fixture = SQLAlchemyFixture(
        env={'CategoryData':Category},
        engine=metadata.bind
    )
    
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
    
    clear_mappers()
    mapper(Category, categories)
        
    data = fixture.data(CategoryData)
    data.setup()
    data.teardown()
    
    fixture.dispose()
    
    # cannot use fixture anymore :
    try:
        data.setup()
    except InvalidRequestError:
        pass
    else:
        assert False, "data.setup() did not raise InvalidRequestError after connection was disposed"
    
    # a new instance of everything is needed :
    metadata.create_all()
    fixture = SQLAlchemyFixture(
        env={'CategoryData':Category},
        engine=metadata.bind
    )
    data = fixture.data(CategoryData)
    data.setup()
    data.teardown()
        
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_session_and_conn():
    class StubConnection:
        def begin(self):
            pass
    stub_conn = StubConnection()
    class StubTransaction:
        def add(self, engine):
            pass
    fake_out_bind = 1
    class StubSession:
        bind_to = fake_out_bind
        def create_transaction(self):
            return StubTransaction()
    stub_session = StubSession()
    f = SQLAlchemyFixture(
        session=stub_session, connection=stub_conn)
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.connection, stub_conn)


### was using this to work around postgres deadlocks...

# if dsn.startswith('postgres'):            
#     # postgres will put everything in a transaction, even after a commit,
#     # and it seems that this makes it near impossible to drop tables after a test
#     # (deadlock), so let's fix that...
#     import psycopg2.extensions
#     self.conn.connection.connection.set_isolation_level(
#             psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
