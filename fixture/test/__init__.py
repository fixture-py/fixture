
from nose.tools import raises
from nose.exc import SkipTest

class LoaderTest:
    """given any data set, tests that the loader can handle it.
    """
    loader = None
    
    def assert_dataset_loaded(self, dataset):
        """assert that the dataset was loaded."""
        raise NotImplementedError
    
    def assert_dataset_torn_down(self, dataset):
        """assert that the dataset was torn down."""
        raise NotImplementedError
        
    def dataset(self):
        """returns some dataset."""
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
            @with_fixtures(self.dataset(), affixer=self.affixer)
            def test_loaded_data(fxt):
                assert_dataset_loaded(fxt)
            test_loaded_data()
            
            @with_fixtures(self.dataset(), affixer=self.affixer)
            def test_atomic_load(fxt):
                assert_dataset_loaded(fxt)
                raise RuntimeError
            run_test = raises(RuntimeError)(test_atomic_load)
            run_test()
                
        except SyntaxError:
            raise SkipTest