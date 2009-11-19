
import os, sys
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import StormFixture
from fixture.test import env_supports
from fixture import (
    StormFixture, NamedDataStyle, PaddedNameStyle, CamelAndUndersStyle, 
    DataSet)
from fixture.dataset import MergedSuperSet
from fixture.test.test_loadable import *
from fixture.examples.db.storm_examples import *
from fixture.test import conf



    
from fixture.util import start_debug, stop_debug
#start_debug("fixture.loadable")
#start_debug("fixture.loadable.tree")
#start_debug("fixture.loadable.storm")



def setup():
    if not env_supports.storm: raise SkipTest

class StormFixtureTest:
    fixture = StormFixture(
                        style=( NamedDataStyle() + CamelAndUndersStyle()),
                        dsn=conf.LITE_DSN, env=globals(), 
                        use_transaction=True,
                        dataclass=MergedSuperSet )
        
    def setUp(self, dsn=conf.LITE_DSN):
        """should load the dataset"""
        from storm.uri import URI
        from storm.locals import  create_database, Store
        from storm.tracer import debug
        #debug(1)
        self.store = Store(create_database(URI(dsn)))
        self.fixture.store = self.store
        
        setup_db(self.store)
    
    def tearDown(self):
        """should unload the dataset."""
        store = self.store
        teardown_db(store)
        store.close()
        conf.reset_heavy_dsn()

class StormCategoryTest(StormFixtureTest):
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(self.store.get(Category, dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(self.store.get(Category, dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(self.store.find(Category).count(), 0)
         
class TestStormCategory(
        HavingCategoryData, StormCategoryTest, LoadableTest):
    pass 

class HavingCategoryDataStorable:
    """mixin that adds data to a LoadableTest."""
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
        
class TestStormCategoryStorable(
        HavingCategoryDataStorable, StormCategoryTest, LoadableTest):
    pass
class TestStormCategoryAsDataType(
        HavingCategoryAsDataType, StormCategoryTest, LoadableTest):
    pass

class TestStormPartialLoad(
        StormFixtureTest, LoaderPartialRecoveryTest):        
   def assert_partial_load_aborted(self):
       raise SkipTest("I don't think storm can support this feature")
       
       # t = self.conn.transaction()
       # eq_(Category.select(connection=t).count(), 0)
        
class StormFixtureCascadeTest(StormFixtureTest):
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(self.store.get(Offer,dataset.free_truck.id).name, dataset.free_truck.name)
        
        eq_(self.store.get(Product,
                dataset.truck.id).name,
                dataset.truck.name)
                
        eq_(self.store.get(Category,
                dataset.cars.id).name,
                dataset.cars.name)
        eq_(self.store.get(Category,
                dataset.free_stuff.id).name,
                dataset.free_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(self.store.find(Category).count(), 0)
        eq_(self.store.find(Offer).count(), 0)
        eq_(self.store.find(Product).count(), 0)

class StormFixtureCascadeTestWithHeavyDB(StormFixtureCascadeTest):
    def setUp(self):
        if not conf.HEAVY_DSN:
            raise SkipTest
            
        StormFixtureCascadeTest.setUp(self, dsn=conf.HEAVY_DSN)

class TestStormFixtureCascade(
        HavingOfferProductData, StormFixtureCascadeTest, 
        LoadableTest):
    pass
class TestStormFixtureCascadeWithHeavyDB(
        HavingOfferProductData, StormFixtureCascadeTestWithHeavyDB, 
        LoadableTest):
    pass
class TestStormFixtureCascadeAsType(
        HavingOfferProductAsDataType, StormFixtureCascadeTest, 
        LoadableTest):
    pass
class TestStormFixtureCascadeAsRef(
        HavingReferencedOfferProduct, StormFixtureCascadeTest, 
        LoadableTest):
    pass
class TestStormFixtureCascadeAsRefInherit(
        HavingRefInheritedOfferProduct, StormFixtureCascadeTest, 
        LoadableTest):
    pass
class TestStormFixtureCascadeAsRefInheritWithHeavyDB(
        HavingRefInheritedOfferProduct, StormFixtureCascadeTestWithHeavyDB, 
        LoadableTest):
    pass
            
