
import os
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import Fixture
from fixture.test import env_supports
from fixture.test.test_loader import (  
    LoaderTest, MixinCategoryData, MixinOfferProductData)
from fixture.loader import SOLoader
from fixture.dataset import MergedSuperSet, DataSet
from fixture.style import NamedDataStyle, PaddedNameStyle, CamelAndUndersStyle
from fixture.examples.db.sqlobject_examples import *
from fixture.test.conf import MEM_DSN

def setup():
    if not env_supports.sqlobject: raise SkipTest

class SOLoaderTest(LoaderTest):
    fixture = Fixture(  loader=SOLoader(dsn=MEM_DSN, env=globals()),
                        dataclass=MergedSuperSet,
                        style=( NamedDataStyle() + 
                                PaddedNameStyle(prefix="F_") +
                                CamelAndUndersStyle()) )
        
    def setup(self, dsn=MEM_DSN):
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

class TestSOLoader(MixinCategoryData, SOLoaderTest):
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(F_Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(F_Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(F_Category.select().count(), 0)

class TestSOLoaderForeignKeys(MixinOfferProductData, SOLoaderTest):
    def setUp(self):
        if not conf.POSTGRES_DSN:
            raise SkipTest
            
        SOLoaderTest.setUp(self, dsn=conf.POSTGRES_DSN)
    
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
            