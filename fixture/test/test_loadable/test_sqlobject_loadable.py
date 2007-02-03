
import os
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import SQLObjectFixture
from fixture.test import env_supports
from fixture import SQLObjectFixture
from fixture.dataset import MergedSuperSet, DataSet
from fixture.style import NamedDataStyle, PaddedNameStyle, CamelAndUndersStyle
from fixture.test.test_loadable import *
from fixture.examples.db.sqlobject_examples import *
from fixture.test import conf

def setup():
    if not env_supports.sqlobject: raise SkipTest

class SQLObjectFixtureTest:
    fixture = SQLObjectFixture(
                        style=( NamedDataStyle() + CamelAndUndersStyle()),
                        dsn=conf.MEM_DSN, env=globals(), 
                        use_transaction=False,
                        dataclass=MergedSuperSet )
        
    def setUp(self, dsn=conf.MEM_DSN):
        """should load the dataset"""
        from sqlobject import connectionForURI
        self.conn = connectionForURI(dsn)
        self.conn.debug = 1
        
        self.fixture.connection = self.conn
        self.transaction = self.conn.transaction()
        
        from sqlobject import sqlhub
        sqlhub.threadConnection = self.transaction
        
        setup_db(self.conn)
    
    def tearDown(self):
        """should unload the dataset."""
        teardown_db(self.transaction)
        self.transaction.commit()

class SQLObjectFixturePostgresTest(SQLObjectFixtureTest):
    def setUp(self):
        if not conf.POSTGRES_DSN:
            raise SkipTest
            
        SQLObjectFixtureTest.setUp(self, dsn=conf.POSTGRES_DSN)

class TestSQLObjectFixture(
        HavingCategoryData, SQLObjectFixtureTest, LoaderTest):
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        eq_(Category.select().count(), 0)

class TestSQLObjectPartialLoad(
        SQLObjectFixtureTest, LoaderPartialRecoveryTest):
        
   def assert_partial_load_aborted(self):
       # I don't think sqlobject can support this ...
       raise SkipTest
       
        # t = self.conn.transaction()
        # eq_(Category.select(connection=t).count(), 0)

class TestSQLObjectFixtureForeignKeys(
        HavingOfferProductData, SQLObjectFixturePostgresTest, 
        LoaderTest):
    
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
        eq_(Category.select().count(), 0)
        eq_(Offer.select().count(), 0)
        eq_(Product.select().count(), 0)
            