
from nose.tools import raises
from nose.exc import SkipTest
from fixture.test import env_supports

class LoaderTest:
    """given any data set, tests that the loader can handle it.
    """
    fixture = None
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        raise NotImplementedError
    
    def assert_data_torndown(self, dataset):
        """assert that the dataset was torn down."""
        raise NotImplementedError
        
    def datasets(self):
        """returns some datasets."""
        raise NotImplementedError
    
    def test_with_data(self):
        """test @with_data"""
        
        @self.fixture.with_data(*self.datasets())
        def test_loaded_data(data):
            self.assert_data_loaded(data)
        test_loaded_data()
        self.assert_data_torndown()
        
        @raises(RuntimeError)
        @self.fixture.with_data(*self.datasets())
        def test_atomic_load(fxt):
            self.assert_data_loaded(fxt)
            raise RuntimeError
        test_atomic_load()
        self.assert_data_torndown()
    
    def test_with_data_as_f(self):
        """test with: fixture() as f"""
        if not env_supports.with_statement:
            raise SkipTest
        
        c = """    
        with self.fixture.data(*self.datasets()) as d:
            self.assert_data_loaded(d)
        self.assert_data_torndown()
        """
        eval(c)
        
        @raises(RuntimeError)
        def doomed_with_statement():
            c = """
            with self.fixture.data(*self.datasets()) as d:
                self.assert_data_loaded(d)
                raise RuntimeError
            """
            eval(c)
        doomed_with_statement()
        self.assert_data_torndown()
        