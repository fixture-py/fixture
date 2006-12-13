
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
        eq_(F_Offer.get(dataset.on_sale.id).name, dataset.on_sale.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(F_Category.select().count(), 0)
        eq_(F_Offer.select().count(), 0)
        eq_(F_Product.select().count(), 0)
        
    def datasets(self):
        """returns some datasets."""
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('cars', dict(id=1, name='cars')),
                    ('free_stuff', dict(id=1, name='get free stuff')),)
        
        class ProductData(DataSet):
            class Conf:
                requires = (CategoryData)
            def data(self):
                return (('truck', dict(
                            id=1, 
                            name='truck', 
                            category_id=self.ref.category.cars.id)),)
        
        class OfferData(DataSet):
            class Conf:
                requires = (CategoryData, ProductData)
            def data(self):
                return (
                    ('free_truck', dict(
                            id=1, 
                            premium='free truck!',
                            product_id=self.ref.product.truck.id,
                            category_id=self.ref.category.free_stuff.id)),
                )
        return [OfferData]
            