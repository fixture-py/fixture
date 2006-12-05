
from nose.tools import raises
from nose.exc import SkipTest

class LoaderTest:
    """given any data set, tests that the loader can handle it.
    """
    loader = None
    
    def assert_fixture_loaded(self, dataset):
        """assert that the dataset was loaded."""
        raise NotImplementedError
    
    def assert_fixture_torn_down(self, dataset):
        """assert that the dataset was torn down."""
        raise NotImplementedError
        
    def datasets(self):
        """returns some datasets."""
        raise NotImplementedError
        
    def setup(self):
        """should load the dataset"""
        raise NotImplementedError
    
    def teardown(self):
        """should unload the dataset."""
        raise NotImplementedError
    
    def test_with_fixtures(self):
        """test @with_fixtures
        """
        from fixture import with_fixtures
        try:
            @with_fixtures(*self.datasets(), affixer=self.affixer)
            def test_loaded_data(fxt):
                assert_fixture_loaded(fxt)
            test_loaded_data()
            assert_fixture_torn_down()
            
            @raises(RuntimeError)
            @with_fixtures(*self.datasets(), affixer=self.affixer)
            def test_atomic_load(fxt):
                fixture_loaded(fxt)
                raise RuntimeError
            test_atomic_load()
            assert_fixture_torn_down()
                
        except SyntaxError:
            raise SkipTest