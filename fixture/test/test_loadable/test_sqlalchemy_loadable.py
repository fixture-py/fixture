
import unittest
from nose.tools import eq_, raises
from nose.exc import SkipTest
from fixture import SQLAlchemyFixture
from fixture.dataset import MergedSuperSet
from fixture import (
    SQLAlchemyFixture, NamedDataStyle, CamelAndUndersStyle, TrimmedNameStyle)
from fixture.exc import UninitializedError
from fixture.test import conf, env_supports, attr
from fixture.test.test_loadable import *
from fixture.examples.db.sqlalchemy_examples import *
from fixture.loadable.sqlalchemy_loadable import *

def setup():
    if not env_supports.sqlalchemy: raise SkipTest

def teardown():
    pass

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
        Session = sessionmaker(bind=metadata.bind, autoflush=True, transactional=True)
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
        self.session.clear()
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        self.session.clear()
        eq_(list(self.session.query(Category)), [])


class TestSABinding(unittest.TestCase):
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
        
        Session = sessionmaker(bind=metadata.bind, autoflush=True, transactional=True)
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
        
        self.session.clear()
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        self.session.clear()
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
        Session = sessionmaker(bind=metadata.bind, autoflush=True, transactional=True)
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
        self.session.clear()
        
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
        self.session.clear()
        
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
        self.ScopedSession = scoped_session(sessionmaker(bind=metadata.bind, autoflush=False, transactional=True))
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
        self.session.clear()
        
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        # simulate the application running into some kind of error:
        new_cat = Category()
        new_cat.name = "doomed to non-existance"
        self.session.save(new_cat)
        self.session.rollback()
        self.ScopedSession.remove()
        
        data.teardown()
        self.session.clear()
        
        print [(c.id, c.name) for c in self.session.query(Category).all()]
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
        ScopedSession = scoped_session(sessionmaker(bind=metadata.bind, autoflush=True, transactional=True))
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
        self.session.clear()
        cats = self.session.query(Category).order_by('name').all()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        self.session.clear()
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
        from elixir import objectstore
        
        eq_(len(objectstore.query(self.CategoryEntity).all()), 0)
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        
        eq_(len(objectstore.query(self.CategoryEntity).all()), 2)
        
        data.teardown()
        eq_(objectstore.query(self.CategoryEntity).all(), [])

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
        Session = sessionmaker(bind=metadata.bind, autoflush=True, transactional=True)
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
        self.session.clear()
        
        cats = self.session.execute(categories.select()).fetchall()
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        self.session.clear()
        eq_(self.session.execute(categories.select()).fetchall(), [])

@raises(UninitializedError)
@attr(unit=True)
def test_TableMedium_requires_bound_session():
    stub_medium = {}
    stub_dataset = {}
    m = TableMedium(stub_medium, stub_dataset)
    class StubLoader:
        connection = None
    m.visit_loader(StubLoader())

@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_unbound_session():
    class StubSession:
        bind_to = None
        def create_transaction(self):
            pass
    stub_session = StubSession()
    f = SQLAlchemyFixture(session=stub_session)
    # I think before this would raise an error, but it should not
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.session_context, None)
    eq_(f.connection, None)

@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_unbound_session_04():
    class StubSession:
        bind = None
        def create_transaction(self):
            pass
    stub_session = StubSession()
    f = SQLAlchemyFixture(session=stub_session)
    # I think before this would raise an error, but it should not
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.session_context, None)
    eq_(f.connection, None)
    
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_session():
    tally = []
    class StubConnectedEngine:
        def begin(self):
            tally.append((self.__class__, 'begin'))
    stub_connected_engine = StubConnectedEngine()
    class StubEngine:
        def connect(self):
            return stub_connected_engine
    stub_engine = StubEngine()
    class MockTransaction:
        def add(self, engine):
            tally.append((self.__class__, 'add', engine))
    class StubSession:
        bind_to = stub_engine
        def create_transaction(self):
            return MockTransaction()
    stub_session = StubSession()
    f = SQLAlchemyFixture(session=stub_session)
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.connection, stub_connected_engine)
    eq_(f.session_context, None)
    
    # assert (MockTransaction, 'add', stub_connected_engine) in tally, (
    #     "expected an engine added to the transaction; calls were: %s" % tally)
        
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_session_04():
    tally = []
    class MockTransaction:
        def add(self, engine):
            tally.append((self.__class__, 'add', engine))
    class MultiStub:
        def connect(self):
            return MultiStub()
        def create_transaction(self):
            return MockTransaction()
        def begin(self):
            tally.append((self.__class__, 'begin'))
            return MockTransaction()
    MultiStub.bind = MultiStub()
            
    stub_session = MultiStub()
    f = SQLAlchemyFixture(session=stub_session)
    f.begin()
    eq_(tally[0][0], MultiStub)
    eq_(tally[0][1], 'begin')
    # eq_(tally[0], MockTransaction, "expected an engine added to the transaction; calls were: %s" % tally)
    # eq_(tally[1], 'add', "expected an engine added to the transaction; calls were: %s" % tally)
        
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_scoped_session():
    tally = []
    class StubConnectedEngine:
        pass
    stub_connected_engine = StubConnectedEngine()
    class StubEngine:
        def connect(self):
            return stub_connected_engine
    stub_engine = StubEngine()
    class MockTransaction:
        def add(self, engine):
            tally.append((self.__class__, 'add', engine))
    class StubScopedSession:
        bind = stub_engine
        def create_transaction(self):
            return MockTransaction()
    f = SQLAlchemyFixture(scoped_session=StubScopedSession)
    f.begin()
    assert isinstance(f.session, StubScopedSession), (
        "unexpected session: %s" % f.session)
    eq_(f.connection, stub_connected_engine)
    eq_(f.session_context, None)
    assert (MockTransaction, 'add', stub_connected_engine) in tally, (
        "expected an engine added to the transaction; calls were: %s" % tally)
        
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
    eq_(f.session_context, None)
    
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_session_and_conn_04():
    class StubConnection:
        def begin(self):
            pass
    stub_conn = StubConnection()
    class StubTransaction:
        def add(self, engine):
            pass
    fake_out_bind = 1
    class StubSession:
        # make sure bind is not accessed...
        bind = fake_out_bind
        def create_transaction(self):
            return StubTransaction()
    stub_session = StubSession()
    f = SQLAlchemyFixture(
        session=stub_session, connection=stub_conn)
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.connection, stub_conn)
    eq_(f.session_context, None)
    
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_unbound_context():
    class StubTransaction:
        pass
    class StubSession:
        bind_to = None
        def create_transaction(self):
            return StubTransaction()
    stub_session = StubSession()
    class StubContext:
        current = stub_session
    stub_context = StubContext()
    f = SQLAlchemyFixture(session_context=stub_context)
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.session_context, stub_context)
    eq_(f.connection, None)
    
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_context():
    tally = []
    class StubConnectedEngine:
        def begin(self):
            tally.append((self.__class__, 'begin'))
    stub_connected_engine = StubConnectedEngine()
    class StubEngine:
        def connect(self):
            return stub_connected_engine
    stub_engine = StubEngine()
    class MockTransaction:
        def add(self, engine):
            tally.append((self.__class__, 'add', engine))
    class StubSession:
        bind_to = stub_engine
        def create_transaction(self):
            return MockTransaction()
    stub_session = StubSession()
    class StubContext:
        current = stub_session
    stub_context = StubContext()
    f = SQLAlchemyFixture(session_context=stub_context)
    f.begin()
    eq_(f.session, stub_session)
    eq_(f.connection, stub_connected_engine)
    eq_(f.session_context, stub_context)
    assert (StubConnectedEngine, 'begin') in tally, (
        "expected connection.begin() to be called; calls were %s" % tally)
    # assert (MockTransaction, 'add', stub_connected_engine) in tally, (
    #     "expected an engine added to the transaction; calls were: %s" % tally)
        
@attr(unit=True)
def test_SQLAlchemyFixture_configured_with_bound_scoped_session():
    tally = []
    class StubConnectedEngine:
        def begin(self):
            tally.append((self.__class__, 'begin'))
    stub_connected_engine = StubConnectedEngine()
    class StubEngine:
        def connect(self):
            return stub_connected_engine
    stub_engine = StubEngine()
    class StubScopedSession:
        bind = stub_engine
        @classmethod
        def configure(cls,**kw):
            for k,v in kw.items():
                setattr(cls,k,v)
    f = SQLAlchemyFixture(scoped_session=StubScopedSession)
    f.begin()
    assert isinstance(f.session, StubScopedSession), (
        "unexpected session: %s" % f.session)
    eq_(f.connection, stub_connected_engine)
    eq_(f.Session, StubScopedSession)
    eq_(f.session.__class__, StubScopedSession)
    eq_(f.engine, stub_engine) # because of Session.configure(bind=engine) inside the loader
    assert (StubConnectedEngine, 'begin') in tally, (
        "expected session.begin(); calls were: %s" % tally)


### was using this to work around postgres deadlocks...

# if dsn.startswith('postgres'):            
#     # postgres will put everything in a transaction, even after a commit,
#     # and it seems that this makes it near impossible to drop tables after a test
#     # (deadlock), so let's fix that...
#     import psycopg2.extensions
#     self.conn.connection.connection.set_isolation_level(
#             psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
