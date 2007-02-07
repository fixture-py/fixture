
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import SQLAlchemyFixture
from fixture.dataset import MergedSuperSet
from fixture import SQLAlchemyFixture
from fixture.style import NamedDataStyle, CamelAndUndersStyle
from fixture.test import conf, env_supports
from fixture.test.test_loadable import *
from fixture.examples.db.sqlalchemy_examples import *

# need to pool connections to avoid "too many connections open for non-super user"
shared_conns = {}
def setup():
    if not env_supports.sqlalchemy: raise SkipTest

def teardown():
    for meta, conn in shared_conns.values():
        conn.close()

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

class SQLAlchemyFixtureTest:
    style = (NamedDataStyle() + CamelAndUndersStyle())
    
    def new_fixture(self):
        raise NotImplementedError
                        
    def setUp(self, dsn=conf.MEM_DSN):
        from sqlalchemy import BoundMetaData
        global shared_conns
        if dsn not in shared_conns:
            meta = BoundMetaData(dsn)
            conn = meta.engine.connect()
            shared_conns[dsn] = meta, conn
            
            # to avoid deadlocks resulting from the inserts/selects
            # we are making simply for test assertions (not fixture loading)
            # lets do all that work in autocommit mode...
            if dsn.startswith('postgres'):
                import psycopg2.extensions
                conn.connection.connection.set_isolation_level(
                                    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.meta, self.conn = shared_conns[dsn]
        # self.meta = BoundMetaData(dsn)
        # self.meta.engine.echo = 1
        
        self.session_context = SessionContext(
            lambda: sqlalchemy.create_session(bind_to=self.conn))
            
        self.fixture = self.new_fixture()
        setup_db(self.meta, self.session_context)
    
    def tearDown(self):
        teardown_db(self.meta, self.session_context)

class SQLAlchemyCategoryTest(SQLAlchemyFixtureTest):
    def assert_data_loaded(self, dataset):
        eq_(Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        eq_(len(Category.select()), 0)
        
class TestSQLAlchemyCategoryInContext(
        HavingCategoryData, SessionContextFixture, SQLAlchemyCategoryTest, LoaderTest):
    pass
class TestSQLAlchemyCategory(
        HavingCategoryData, SessionFixture, SQLAlchemyCategoryTest, LoaderTest):
    pass
    

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
        HavingCategoryDataStorable, SessionFixture, SQLAlchemyCategoryTest, LoaderTest):
    pass
class TestSQLAlchemyCategoryStorableInContext(
        HavingCategoryDataStorable, SessionContextFixture, SQLAlchemyCategoryTest, LoaderTest):
    pass
    
    
class TestSQLAlchemyCategoryAsDataType(
        HavingCategoryAsDataType, SessionContextFixture, SQLAlchemyCategoryTest, LoaderTest):
    pass
class TestSQLAlchemyCategoryAsDataTypeInContext(
        HavingCategoryAsDataType, SessionFixture, SQLAlchemyCategoryTest, LoaderTest):
    pass

class SQLAlchemyPartialRecoveryTest(SQLAlchemyFixtureTest):
    def assert_partial_load_aborted(self):
        eq_(len(Category.select()), 0)
        eq_(len(Offer.select()), 0)
        eq_(len(Product.select()), 0)

class TestSQLAlchemyPartialRecoveryInContext(
        SessionContextFixture, SQLAlchemyPartialRecoveryTest, LoaderPartialRecoveryTest):
    pass
class TestSQLAlchemyPartialRecovery(
        SessionFixture, SQLAlchemyPartialRecoveryTest, LoaderPartialRecoveryTest):
    pass

class SQLAlchemyFixtureForKeysTest(SQLAlchemyFixtureTest):
    def setUp(self):
        if not conf.POSTGRES_DSN:
            raise SkipTest
            
        SQLAlchemyFixtureTest.setUp(self, dsn=conf.POSTGRES_DSN)
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(Offer.get(dataset.free_truck.id).name, dataset.free_truck.name)
        
        product = Product.get(dataset.truck.id)
        eq_(product.name, dataset.truck.name)
        eq_(product.category_id, dataset.cars.id)
        
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
        
class TestSQLAlchemyFixtureForKeysInContext(
        HavingOfferProductData, SessionContextFixture, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
class TestSQLAlchemyFixtureForKeys(
        HavingOfferProductData, SessionFixture, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
class TestSQLAlchemyFixtureForKeysAsTypeInContext(
        HavingOfferProductAsDataType, SessionContextFixture, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
class TestSQLAlchemyFixtureForKeysAsType(
        HavingOfferProductAsDataType, SessionFixture, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
class TestSQLAlchemyFixtureSeqForKeysInContext(
        HavingSequencedOfferProduct, SessionContextFixture, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
class TestSQLAlchemyFixtureSeqForKeys(
        HavingSequencedOfferProduct, SessionFixture, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
    