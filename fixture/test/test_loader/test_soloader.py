
import os
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import Fixture
from fixture.test import env_supports
from fixture.test.test_loader import LoaderTest
from fixture.loader import SOLoader
from fixture.dataset import MergedSuperSet, DataSet
from fixture.style import NamedDataStyle, PaddedNameStyle, CamelAndUndersStyle
from fixture.examples.db.sqlobject_examples import *

DSN = 'sqlite:/:memory:'

def setup():
    if not env_supports.sqlobject: raise SkipTest

class SOLoaderTest(LoaderTest):
    fixture = Fixture(  loader=SOLoader(dsn=DSN, env=globals()),
                        dataclass=MergedSuperSet,
                        style=( NamedDataStyle() + 
                                PaddedNameStyle(prefix="F_") +
                                CamelAndUndersStyle()) )
        
    def setup(self, dsn=DSN):
        """should load the dataset"""
        from sqlobject import connectionForURI
        self.conn = connectionForURI(dsn)
        setup_db(self.conn)
        
        from sqlobject import sqlhub
        sqlhub.processConnection = self.conn
    
    def teardown(self):
        """should unload the dataset."""
        teardown_db(self.conn)
        from sqlobject import sqlhub
        sqlhub.processConnection = None

class TestSOLoader(SOLoaderTest):
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(F_Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(F_Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(F_Category.select().count(), 0)
        
    def datasets(self):
        """returns some datasets."""
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('gray_stuff', dict(id=1, name='gray')),
                    ('yellow_stuff', dict(id=2, name='yellow')),
                )
        return [CategoryData]

class TestSOLoaderForeignKeys(SOLoaderTest):
    def setUp(self):
        if not os.environ.get('FIXTURE_TEST_DSN_PG'):
            raise SkipTest
        SOLoaderTest.setUp(self, dsn=os.environ['FIXTURE_TEST_DSN_PG'])
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(F_Offer.get(dataset.free_truck.id).name, dataset.free_truck.name)
        
        eq_(F_Product.get(
                dataset.truck.id).name,
                dataset.truck.name)
                
        eq_(F_Category.get(
                dataset.cars.id).name,
                dataset.cars.name)
        eq_(F_Category.get(
                dataset.free_stuff.id).name,
                dataset.free_stuff.name)
        
        eq_(dataset.just_some_widget.type, 'foobar')
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(F_Category.select().count(), 0)
        eq_(F_Offer.select().count(), 0)
        eq_(F_Product.select().count(), 0)
        
    def datasets(self):
        """returns some datasets."""
        
        class WidgetData(DataSet):
            def data(self):
                return (('just_some_widget', dict(type='foobar')),)
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('cars', dict(id=1, name='cars')),
                    ('free_stuff', dict(id=2, name='get free stuff')),)
        
        class ProductData(DataSet):
            class Config:
                requires = (CategoryData,)
            def data(self):
                return (('truck', dict(
                            id=1, 
                            name='truck', 
                            category_id=self.ref.CategoryData.cars.id)),)
        
        class OfferData(DataSet):
            class Config:
                requires = (CategoryData, ProductData)
                references = (WidgetData,)
            def data(self):
                return (
                    ('free_truck', dict(
                            id=1, 
                            name=('free truck by %s' % 
                                    self.ref.WidgetData.just_some_widget.type),
                            product_id=self.ref.ProductData.truck.id,
                            category_id=self.ref.CategoryData.free_stuff.id)),
                )
        return [OfferData, ProductData]
            