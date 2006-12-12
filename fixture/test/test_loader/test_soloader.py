
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import Fixture
from fixture.test import env_supports
from fixture.test.test_loader import LoaderTest
from fixture.loader import SOLoader
from fixture.dataset import MergedSuperSet
from fixture.style import NamedDataStyle, PaddedNameStyle, CamelAndUndersStyle
from fixture.examples.db.sqlobject_fixtures import *

DSN = 'sqlite:/:memory:'

def setup():
    if not env_supports.sqlobject: raise SkipTest

class test_SOLoader_can_load(LoaderTest):
    fixture = Fixture(  loader=SOLoader(dsn=DSN, env=globals()),
                        dataclass=MergedSuperSet,
                        style=( NamedDataStyle() + 
                                PaddedNameStyle(prefix="F_") +
                                CamelAndUndersStyle()) )
    
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
        from fixture import DataSet
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('gray_stuff', dict(id=1, name='gray')),
                    ('yellow_stuff', dict(id=2, name='yellow')),
                )
        return [CategoryData]
        
    def setup(self):
        """should load the dataset"""
        from sqlobject import connectionForURI
        self.conn = connectionForURI(DSN)
        setup_db(self.conn)
        
        from sqlobject import sqlhub
        sqlhub.processConnection = self.conn
    
    def teardown(self):
        """should unload the dataset."""
        teardown_db(self.conn)
        from sqlobject import sqlhub
        sqlhub.processConnection = None