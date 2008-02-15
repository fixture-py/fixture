
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
    
class HavingCategoryData(HavingCategoryData):
    # it's the same as the generic category dataset except for sqlalchemy we 
    # need the mapper itself for some tests
    MappedCategory = Category

class DefaultFixture(object):
    def new_fixture(self):
        return SQLAlchemyFixture(  
                        style=self.style,
                        env=globals(),
                        dataclass=MergedSuperSet )

class SessionContextFixture(object):
    def new_fixture(self):
        return SQLAlchemyFixture(  
                        session_context=self.session_context,
                        style=self.style,
                        env=globals(),
                        dataclass=MergedSuperSet )

class SessionFixture(object):
    def new_fixture(self):
        return SQLAlchemyFixture(  
                        session=self.session_context.current,
                        style=self.style,
                        env=globals(),
                        dataclass=MergedSuperSet )

class SQLAlchemyFixtureTest(object):
    style = (NamedDataStyle() + CamelAndUndersStyle())
    
    def new_fixture(self):
        raise NotImplementedError
                        
    def setUp(self, dsn=conf.LITE_DSN):
        from sqlalchemy import MetaData
        from sqlalchemy.orm import clear_mappers, create_session
        from fixture.examples.db.sqlalchemy_examples import (
            metadata, Category, categories, Product, products, Offer, offers)

        clear_mappers()
        
        self.engine = create_engine(dsn)
        self.meta = MetaData(self.engine)
        self.conn = self.engine.connect()
        
        self.session_context = SessionContext(
            lambda: create_session(bind=self.conn))
        
        c = self.session_context
        self.fixture = self.new_fixture()
        assign_mapper(c, Category, categories)
        assign_mapper(c, Product, products, properties={
            'category': relation(Category),
        })
        assign_mapper(c, Offer, offers, properties={
            'category': relation(Category, backref='products'),
            'product': relation(Product)
        })
        self.meta.create_all()
        # setup_db(self.meta, self.session_context)
    
    def tearDown(self):
        import sqlalchemy.orm
        self.meta.drop_all()
        sqlalchemy.orm.clear_mappers()
        self.conn.close()
        self.engine.dispose()
        self.session_context.current.clear()

class SQLAlchemyCategoryTest(SQLAlchemyFixtureTest):
    def assert_data_loaded(self, dataset):
        eq_(Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        eq_(len(Category.select()), 0)
        
class TestSQLAlchemyCategoryInContext(
        HavingCategoryData, SessionContextFixture, 
        SQLAlchemyCategoryTest, LoadableTest):
    pass
class TestSQLAlchemyCategory(
        HavingCategoryData, SessionFixture, SQLAlchemyCategoryTest, 
        LoadableTest):
    pass
class TestSQLAlchemyCategoryInDefault(HavingCategoryData):
    style = (NamedDataStyle() + CamelAndUndersStyle())
    
    def setUp(self, dsn=conf.HEAVY_DSN):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import mapper
        from sqlalchemy.orm import clear_mappers
        from fixture.loadable.sqlalchemy_loadable import Session
        from fixture.examples.db.sqlalchemy_examples import (
            metadata, Category, categories, Product, products, Offer, offers)

        clear_mappers()
        self.engine = create_engine(dsn)
        self.conn = self.engine.connect()
        
        metadata.create_all(bind=self.engine)
        self.fixture = SQLAlchemyFixture(  
                            style=self.style,
                            connection=self.conn,
                            dataclass=MergedSuperSet,
                            env=globals() )
        
        if dsn.startswith('postgres'):            
            # postgres will put everything in a transaction, even after a commit,
            # and it seems that this makes it near impossible to drop tables after a test
            # (deadlock)
            import psycopg2.extensions
            self.conn.connection.connection.set_isolation_level(
                    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    
    def tearDown(self):
        from fixture.examples.db.sqlalchemy_examples import metadata
        import sqlalchemy.orm
        metadata.drop_all(bind=self.engine)
        sqlalchemy.orm.clear_mappers()
        # self.conn.close()
        # self.engine.dispose()
    
    def test_colliding_sessions(self):
        from fixture.examples.db.sqlalchemy_examples import (Category, Product, Offer)
        from sqlalchemy.exceptions import IntegrityError
        from sqlalchemy.orm import sessionmaker, scoped_session
        from fixture.loadable.sqlalchemy_loadable import Session as FixtureSession
        
        mapper(Category, categories)
        mapper(Product, products, properties={
            'category': relation(Category),
        })
        mapper(Offer, offers, properties={
            'category': relation(Category, backref='products'),
            'product': relation(Product)
        })
        
        Session = scoped_session(sessionmaker(autoflush=True, transactional=True))
        Session.configure(bind=self.conn)
        
        eq_(len(Session.query(Category).all()), 0)
        
        datasets = self.datasets()
        data = self.fixture.data(*datasets)
        data.setup()
        
        # two rows in datasets
        eq_(len(FixtureSession.query(Category).all()), 2)
        eq_(len(Session.query(Category).all()), 2)
        
        session = Session()
        trans = self.conn.begin()
        prod = Product()
        session.save(prod)
        session.flush()
        trans.rollback()
        session.close()
        
        data.teardown()
        eq_(FixtureSession.query(Category).all(), [])
        eq_(Session.query(Category).all(), [])
    
    def test_colliding_sessions_with_assigned_mappers(self):
        from fixture.examples.db.sqlalchemy_examples import (Category, Product, Offer)
        from sqlalchemy.exceptions import IntegrityError
        from sqlalchemy.orm import sessionmaker, scoped_session
        from fixture.loadable.sqlalchemy_loadable import Session as FixtureSession
        
        Session = scoped_session(sessionmaker(autoflush=False, transactional=True))
        Session.configure(bind=self.conn)
        
        Session.mapper(Category, categories, save_on_init=False)
        Session.mapper(Product, products, properties={
            'category': relation(Category),
        }, save_on_init=False)
        Session.mapper(Offer, offers, properties={
            'category': relation(Category, backref='products'),
            'product': relation(Product)
        }, save_on_init=False)
        
        eq_(len(Session.query(Category).all()), 0)
        
        datasets = self.datasets()
        data = self.fixture.data(*datasets)
        data.setup()
        
        # two rows in datasets
        eq_(len(FixtureSession.query(Category).all()), 2)
        eq_(len(Session.query(Category).all()), 2)
        
        session = Session()
        trans = self.conn.begin()
        prod = Product()
        session.save(prod)
        session.flush()
        trans.rollback()
        session.close()
        
        data.teardown()
        eq_(FixtureSession.query(Category).all(), [])
        eq_(Session.query(Category).all(), [])
        
    def test_colliding_sessions_with_elixir(self):
        from sqlalchemy.exceptions import IntegrityError
        from sqlalchemy.orm import sessionmaker, scoped_session
        from fixture.loadable.sqlalchemy_loadable import Session as FixtureSession
        from elixir import Entity, using_options, using_mapper_options, OneToMany, ManyToOne, setup_all
        
        Session = scoped_session(sessionmaker(autoflush=False, transactional=True))
        Session.configure(bind=self.conn)
        
        class CategoryEntity(Entity):
            products = OneToMany('ProductEntity')
            using_options(tablename=str(categories))
            using_mapper_options(save_on_init=False)
            
        class ProductEntity(Entity):
            category = ManyToOne('CategoryEntity')
            offers = OneToMany('OfferEntity')
            using_options(tablename=str(products))
            using_mapper_options(save_on_init=False)
            
        class OfferEntity(Entity):
            product = ManyToOne('ProductEntity')
            using_options(tablename=str(offers))
            using_mapper_options(save_on_init=False)
        
        setup_all()
        
        self.fixture.env = {'Category':CategoryEntity, 'Product':ProductEntity, 'Offer':OfferEntity}
        
        eq_(len(Session.query(CategoryEntity).all()), 0)
        
        datasets = self.datasets()
        data = self.fixture.data(*datasets)
        data.setup()
        
        # two rows in datasets
        eq_(len(FixtureSession.query(CategoryEntity).all()), 2)
        eq_(len(Session.query(CategoryEntity).all()), 2)
        
        session = Session()
        trans = self.conn.begin()
        prod = ProductEntity()
        session.save(prod)
        session.flush()
        trans.rollback()
        session.close()
        
        data.teardown()
        eq_(FixtureSession.query(CategoryEntity).all(), [])
        eq_(Session.query(CategoryEntity).all(), [])

class HavingCategoryDataStorable:
    def datasets(self):
        class WhateverIWantToCallIt(DataSet):
            class Meta:
                storable = Category
            class gray_stuff:
                id=1
                name='gray'
            class yellow_stuff:
                id=2
                name='yellow'
        return [WhateverIWantToCallIt]
        
class TestSQLAlchemyCategoryStorable(
        HavingCategoryDataStorable, SessionFixture, 
        SQLAlchemyCategoryTest, LoadableTest):
    pass
class TestSQLAlchemyCategoryStorableInContext(
        HavingCategoryDataStorable, SessionContextFixture, 
        SQLAlchemyCategoryTest, LoadableTest):
    pass

class TestSQLAlchemyCategoryPrefixed(
        SQLAlchemyCategoryTest, LoadableTest):
    """test finding and loading Category, using a data set named with a prefix 
    and a data suffix style
    """
    def new_fixture(self):
        return SQLAlchemyFixture(  
                    session=self.session_context.current,
                    style=(TrimmedNameStyle(prefix="Foo_") + NamedDataStyle()),
                    env=globals(),
                    dataclass=MergedSuperSet )
                        
    def datasets(self):
        class Foo_CategoryData(DataSet):
            class gray_stuff:
                id=1
                name='gray'
            class yellow_stuff:
                id=2
                name='yellow'
        return [Foo_CategoryData]

class HavingMappedCategory(object):
    class MappedCategory(object):
        pass
    
    def datasets(self):
        from sqlalchemy import mapper
        mapper(self.MappedCategory, categories)
        
        class CategoryData(DataSet):
            class Meta:
                storable = self.MappedCategory
            class gray_stuff:
                id=1
                name='gray'
            class yellow_stuff:
                id=2
                name='yellow'
        return [CategoryData]
    
class TestSQLAlchemyMappedCategory(
        HavingMappedCategory, SessionContextFixture, SQLAlchemyCategoryTest, 
        LoadableTest):
    pass


class SQLAlchemyCatExplicitDeleteTest(SQLAlchemyCategoryTest):
    """test that an explicitly deleted object isn't deleted again.
    
    thanks to Allen Bierbaum for this test case.
    """
    def assert_data_loaded(self, data):
        super(SQLAlchemyCatExplicitDeleteTest, self).assert_data_loaded(data)
        
        # explicitly delete the object to assert that 
        # teardown avoids the conflict :
        session = self.session_context.current
        cat = session.query(self.MappedCategory).get(data.gray_stuff.id)
        session.delete(cat)
        session.flush()
    
class TestSQLAlchemyCategoryExplicitDelete(
        HavingMappedCategory, SessionContextFixture, 
        SQLAlchemyCatExplicitDeleteTest, LoadableTest):
    pass    
class TestSQLAlchemyAssignedCategoryExplicitDelete(
        HavingCategoryData, SessionContextFixture, 
        SQLAlchemyCatExplicitDeleteTest, LoadableTest):
    pass
    
    
class TestSQLAlchemyCategoryAsDataType(
        HavingCategoryAsDataType, SessionContextFixture, 
        SQLAlchemyCategoryTest, LoadableTest):
    pass
class TestSQLAlchemyCategoryAsDataTypeInContext(
        HavingCategoryAsDataType, SessionFixture, 
        SQLAlchemyCategoryTest, LoadableTest):
    pass

class SQLAlchemyPartialRecoveryTest(SQLAlchemyFixtureTest):
    def assert_partial_load_aborted(self):
        eq_(len(Category.select()), 0)
        eq_(len(Offer.select()), 0)
        eq_(len(Product.select()), 0)

class TestSQLAlchemyPartialRecoveryInContext(
        SessionContextFixture, SQLAlchemyPartialRecoveryTest, 
        LoaderPartialRecoveryTest):
    pass
class TestSQLAlchemyPartialRecovery(
        SessionFixture, SQLAlchemyPartialRecoveryTest, 
        LoaderPartialRecoveryTest):
    pass

class SQLAlchemyFixtureForKeysTest(SQLAlchemyFixtureTest):
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(Offer.get(dataset.free_truck.id).name, dataset.free_truck.name)
        
        product = Product.query().join('category').get(dataset.truck.id)
        eq_(product.name, dataset.truck.name)
        eq_(product.category.id, dataset.cars.id)
        
        category = Category.get(dataset.cars.id)
        eq_(category.name, dataset.cars.name)
        
        eq_(Category.get(
                dataset.free_stuff.id).name,
                dataset.free_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(len(Category.select()), 0)
        eq_(len(Offer.select()), 0)
        eq_(len(Product.select()), 0)

class SQLAlchemyFixtureForKeysTestWithPsql(SQLAlchemyFixtureForKeysTest):
    def setUp(self):
        if not conf.HEAVY_DSN:
            raise SkipTest
            
        SQLAlchemyFixtureForKeysTest.setUp(self, dsn=conf.HEAVY_DSN)
        
class TestSQLAlchemyFixtureForKeys(
        HavingOfferProductData, SessionFixture, 
        SQLAlchemyFixtureForKeysTest, LoadableTest):
    pass
class TestSQLAlchemyFixtureForKeysWithHeavyDB(
        HavingOfferProductData, SessionFixture, 
        SQLAlchemyFixtureForKeysTestWithPsql, LoadableTest):
    pass
class TestSQLAlchemyFixtureForKeysInContext(
        HavingOfferProductData, SessionContextFixture, 
        SQLAlchemyFixtureForKeysTest, LoadableTest):
    pass
    
class TestSQLAlchemyFixtureForKeysAsType(
        HavingOfferProductAsDataType, SessionFixture, 
        SQLAlchemyFixtureForKeysTest, LoadableTest):
    pass
class TestSQLAlchemyFixtureForKeysAsTypeInContext(
        HavingOfferProductAsDataType, SessionContextFixture, 
        SQLAlchemyFixtureForKeysTest, LoadableTest):
    pass
class TestSQLAlchemyFixtureForKeysAsTypeInContextWithHeavyDB(
        HavingOfferProductAsDataType, SessionContextFixture, 
        SQLAlchemyFixtureForKeysTestWithPsql, LoadableTest):
    pass
    
class TestSQLAlchemyFixtureRefForKeys(
        HavingReferencedOfferProduct, SessionFixture, 
        SQLAlchemyFixtureForKeysTest, LoadableTest):
    pass
    
class TestSQLAlchemyFixtureRefInheritForKeys(
        HavingRefInheritedOfferProduct, SessionFixture, 
        SQLAlchemyFixtureForKeysTest, LoadableTest):
    pass
class TestSQLAlchemyFixtureRefInheritForKeysWithHeavyDB(
        HavingRefInheritedOfferProduct, SessionFixture, 
        SQLAlchemyFixtureForKeysTestWithPsql, LoadableTest):
    pass

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
