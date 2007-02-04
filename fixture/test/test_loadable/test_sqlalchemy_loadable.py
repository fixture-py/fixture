
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import SQLAlchemyFixture
from fixture.dataset import MergedSuperSet
from fixture import SQLAlchemyFixture
from fixture.style import NamedDataStyle, CamelAndUndersStyle
from fixture.test import conf, env_supports
from fixture.test.test_loadable import *
from fixture.examples.db.sqlalchemy_examples import *
    
def setup():
    if not env_supports.sqlalchemy: raise SkipTest

class SQLAlchemyFixtureTest:
    fixture = SQLAlchemyFixture(  
                        style=(NamedDataStyle() + CamelAndUndersStyle()),
                        env=globals(),
                        dataclass=MergedSuperSet )
        
    def setUp(self, dsn=conf.MEM_DSN):
        from sqlalchemy import BoundMetaData
        
        self.meta = BoundMetaData(dsn)
        self.meta.engine.echo = 1
        self.fixture.meta = self.meta
        
        self.session_context = SessionContext(
            lambda: sqlalchemy.create_session(bind_to=self.meta.engine))
        self.fixture.session_context = self.session_context
        
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
        
class TestSQLAlchemyCategory(
        HavingCategoryData, SQLAlchemyCategoryTest, LoaderTest):
    pass
class TestSQLAlchemyCategoryAsDataType(
        HavingCategoryAsDataType, SQLAlchemyCategoryTest, LoaderTest):
    pass

class TestSQLAlchemyPartialRecovery(
        SQLAlchemyFixtureTest, LoaderPartialRecoveryTest):
    
    def assert_partial_load_aborted(self):
        eq_(len(Category.select()), 0)
        eq_(len(Offer.select()), 0)
        eq_(len(Product.select()), 0)

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
        
class TestSQLAlchemyFixtureForKeys(
        HavingOfferProductData, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
        
class TestSQLAlchemyFixtureForKeysAsType(
        HavingOfferProductAsDataType, SQLAlchemyFixtureForKeysTest, LoaderTest):
    pass
    