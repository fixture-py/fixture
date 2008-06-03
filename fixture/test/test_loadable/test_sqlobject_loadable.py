
import os, sys
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import SQLObjectFixture
from fixture.test import env_supports
from fixture import (
    SQLObjectFixture, NamedDataStyle, PaddedNameStyle, CamelAndUndersStyle, 
    DataSet)
from fixture.dataset import MergedSuperSet
from fixture.test.test_loadable import *
from fixture.examples.db.sqlobject_examples import *
from fixture.test import conf

def setup():
    if not env_supports.sqlobject: raise SkipTest

class SQLObjectFixtureTest:
    fixture = SQLObjectFixture(
                        style=( NamedDataStyle() + CamelAndUndersStyle()),
                        dsn=conf.LITE_DSN, env=globals(), 
                        use_transaction=False,
                        dataclass=MergedSuperSet )
        
    def setUp(self, dsn=conf.LITE_DSN):
        """should load the dataset"""
        from sqlobject import connectionForURI
        self.conn = connectionForURI(dsn)
        self.fixture.connection = self.conn
        
        from sqlobject import sqlhub
        sqlhub.processConnection = self.conn
        
        setup_db(self.conn)
    
    def tearDown(self):
        """should unload the dataset."""
        conn = self.conn
        teardown_db(conn)
        conn.close()
        conf.reset_heavy_dsn()

class SQLObjectCategoryTest(SQLObjectFixtureTest):
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(Category.select().count(), 0)
         
class TestSQLObjectCategory(
        HavingCategoryData, SQLObjectCategoryTest, LoadableTest):
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
        
class TestSQLObjectCategoryStorable(
        HavingCategoryDataStorable, SQLObjectCategoryTest, LoadableTest):
    pass
class TestSQLObjectCategoryAsDataType(
        HavingCategoryAsDataType, SQLObjectCategoryTest, LoadableTest):
    pass

class TestSQLObjectPartialLoad(
        SQLObjectFixtureTest, LoaderPartialRecoveryTest):        
   def assert_partial_load_aborted(self):
       raise SkipTest("I don't think sqlobject can support this feature")
       
       # t = self.conn.transaction()
       # eq_(Category.select(connection=t).count(), 0)
        
class SQLObjectFixtureCascadeTest(SQLObjectFixtureTest):
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
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(Category.select().count(), 0)
        eq_(Offer.select().count(), 0)
        eq_(Product.select().count(), 0)

class SQLObjectFixtureCascadeTestWithHeavyDB(SQLObjectFixtureCascadeTest):
    def setUp(self):
        if not conf.HEAVY_DSN:
            raise SkipTest
            
        SQLObjectFixtureCascadeTest.setUp(self, dsn=conf.HEAVY_DSN)

class TestSQLObjectFixtureCascade(
        HavingOfferProductData, SQLObjectFixtureCascadeTest, 
        LoadableTest):
    pass
class TestSQLObjectFixtureCascadeWithHeavyDB(
        HavingOfferProductData, SQLObjectFixtureCascadeTestWithHeavyDB, 
        LoadableTest):
    pass
class TestSQLObjectFixtureCascadeAsType(
        HavingOfferProductAsDataType, SQLObjectFixtureCascadeTest, 
        LoadableTest):
    pass
class TestSQLObjectFixtureCascadeAsRef(
        HavingReferencedOfferProduct, SQLObjectFixtureCascadeTest, 
        LoadableTest):
    pass
class TestSQLObjectFixtureCascadeAsRefInherit(
        HavingRefInheritedOfferProduct, SQLObjectFixtureCascadeTest, 
        LoadableTest):
    pass
class TestSQLObjectFixtureCascadeAsRefInheritWithHeavyDB(
        HavingRefInheritedOfferProduct, SQLObjectFixtureCascadeTestWithHeavyDB, 
        LoadableTest):
    pass
            