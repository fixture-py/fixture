
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

# getting too many open connections error...
dsn_conns = {}

def setup():
    if not env_supports.sqlobject: raise SkipTest

def teardown():
    for dsn, conn in dsn_conns.items():
        conn.close()
        del dsn_conns[dsn]

class SQLObjectFixtureTest:
    fixture = SQLObjectFixture(
                        style=( NamedDataStyle() + CamelAndUndersStyle()),
                        dsn=conf.MEM_DSN, env=globals(), 
                        use_transaction=False,
                        dataclass=MergedSuperSet )
        
    def setUp(self, dsn=conf.MEM_DSN):
        """should load the dataset"""
        from sqlobject import connectionForURI
        if dsn not in dsn_conns:
            dsn_conns[dsn] = connectionForURI(dsn)
        self.conn = dsn_conns[dsn]
        # self.conn.debug = 1
        
        self.fixture.connection = self.conn
        self.transaction = self.conn.transaction()
        
        from sqlobject import sqlhub
        sqlhub.threadConnection = self.transaction
        
        setup_db(self.conn)
    
    def tearDown(self):
        """should unload the dataset."""
        teardown_db(self.transaction)
        self.transaction.commit()

class SQLObjectFixtureForKeysTest(SQLObjectFixtureTest):
    def setUp(self):
        if not conf.POSTGRES_DSN:
            raise SkipTest
            
        SQLObjectFixtureTest.setUp(self, dsn=conf.POSTGRES_DSN)

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
        HavingCategoryData, SQLObjectCategoryTest, LoaderTest):
    pass
    
class TestSQLObjectCategoryAsDataType(
        HavingCategoryAsDataType, SQLObjectCategoryTest, LoaderTest):
    pass

class TestSQLObjectPartialLoad(
        SQLObjectFixtureTest, LoaderPartialRecoveryTest):        
   def assert_partial_load_aborted(self):
       # I don't think sqlobject can support this ...
       raise SkipTest
       
        # t = self.conn.transaction()
        # eq_(Category.select(connection=t).count(), 0)
        
class SQLObjectFixtureCascadeTest(SQLObjectFixtureForKeysTest):
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

class TestSQLObjectFixtureCascade(
        HavingOfferProductData, SQLObjectFixtureCascadeTest, 
        LoaderTest):
    pass
class TestSQLObjectFixtureCascadeAsType(
        HavingOfferProductAsDataType, SQLObjectFixtureCascadeTest, 
        LoaderTest):
    pass
class TestSQLObjectFixtureSeqCascade(
        HavingSequencedOfferProduct, SQLObjectFixtureCascadeTest, 
        LoaderTest):
    pass
            