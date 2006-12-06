
from nose.tools import eq_
from nose.exc import SkipTest
from fixture.test.helpers import LoaderTest
try:
    from fixture.loader import SOLoader
except ImportError:
    SOLoader = None
try:
    import sqlobject
except ImportError:
    sqlobject = None
from fixture.examples.db.sqlobject_fixtures import *

def setup():
    if not sqlobject: raise SkipTest

class test_SOLoader_can_load_one(LoaderTest):
    loader = SOLoader    
    
    def assert_fixture_loaded(self, dataset):
        """assert that the dataset was loaded."""
        eq_(F_Category.get( dataset.gray_stuff.id).name, 
                            dataset.gray_stuff.name)
        eq_(F_Category.get( dataset.yellow_stuff.id).name, 
                            dataset.yellow_stuff.name)
    
    def assert_fixture_torn_down(self, dataset):
        """assert that the dataset was torn down."""
        eq_(F_Category.select().count(), 0)
        
    def datasets(self):
        """returns some datasets."""
        from fixture import DataSet
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('gray_stuff', dict(id=1, name=gray)),
                    ('yellow_stuff', dict(id=2, name=yellow)),
                )
        return [CategoryData]
        
    def setup(self):
        """should load the dataset"""
        LoaderTest.setup(self)
        from sqlobject import connectionForURI
        self.conn = connectionForURI("sqlite:/:memory:")
        setup_db(self.conn)
        
        from sqlobject import sqlhub
        sqlhub.processConnection = self.conn
    
    def teardown(self):
        """should unload the dataset."""
        LoaderTest.teardown(self)
        teardown_db(self.conn)
        from sqlobject import sqlhub
        sqlhub.processConnection = None