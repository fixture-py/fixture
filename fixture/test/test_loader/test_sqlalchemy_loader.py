
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import Fixture
from fixture.dataset import MergedSuperSet
from fixture.loader import SqlAlchemyLoader
from fixture.test.test_loader import (  
    LoaderTest, HavingCategoryData, HavingOfferProductData)
from fixture.style import NamedDataStyle, CamelAndUndersStyle
from fixture.test import conf, env_supports
from fixture.examples.db.sqlalchemy_examples import *
    
def setup():
    if not env_supports.sqlalchemy: raise SkipTest

class SqlAlchemyLoaderTest(LoaderTest):
    fixture = Fixture(  loader=SqlAlchemyLoader(env=globals()),
                        dataclass=MergedSuperSet,
                        style=(NamedDataStyle() + CamelAndUndersStyle()) )
        
    def setup(self, dsn=conf.MEM_DSN):
        from sqlalchemy import BoundMetaData
        
        self.meta = BoundMetaData(dsn)
        self.fixture.loader.meta = self.meta
        
        self.session_context = SessionContext(
            lambda: sqlalchemy.create_session(bind_to=self.meta.engine))
        self.fixture.loader.session_context = self.session_context
        
        setup_db(self.meta, self.session_context)
    
    def teardown(self):
        teardown_db(self.meta, self.session_context)

class TestSqlAlchemy(HavingCategoryData, SqlAlchemyLoaderTest):
    def assert_data_loaded(self, dataset):
        eq_(Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        eq_(len(Category.select()), 0)
        
class TestSqlAlchemyLoaderForeignKeys(
                            HavingOfferProductData, SqlAlchemyLoaderTest):
    def setUp(self):
        if not conf.POSTGRES_DSN:
            raise SkipTest
            
        SqlAlchemyLoaderTest.setUp(self, dsn=conf.POSTGRES_DSN)
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(Offer.get(dataset.free_truck.id).name, dataset.free_truck.name)
        
        eq_(Product.get(
                dataset.truck.id).name,
                dataset.truck.name)
                
        eq_(Category.get(
                dataset.cars.id).name,
                dataset.cars.name)
        eq_(Category.get(
                dataset.free_stuff.id).name,
                dataset.free_stuff.name)
        
        eq_(dataset.just_some_widget.type, 'foobar')
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(len(Category.select()), 0)
        eq_(len(Offer.select()), 0)
        eq_(len(Product.select()), 0)
        