
"""helper tools for the fixture.test suite."""

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
        
        @with_fixtures(*self.datasets())
        def test_loaded_data(fxt):
            self.assert_fixture_loaded(fxt)
        test_loaded_data()
        self.assert_fixture_torn_down()
        
        @raises(RuntimeError)
        @with_fixtures(*self.datasets())
        def test_atomic_load(fxt):
            fixture_loaded(fxt)
            raise RuntimeError
        test_atomic_load()
        self.assert_fixture_torn_down()
    
    def test_fixtures_using_with(self):
        """test with: fixtures() as f"""
        from fixture import fixtures
        try:
            with
        except NameError:
            raise SkipTest
        
        c = """    
        with fixtures(*self.datasets()) as fxt:
            self.assert_fixture_loaded(fxt)
        self.assert_fixture_torn_down()
        """
        eval(c)
        
        @raises(RuntimeError)
        def doomed_with_statement():
            c = """
            with fixtures(*self.datasets()) as fxt:
                self.assert_fixture_loaded(fxt)
                raise RuntimeError
            """
            eval(c)
        doomed_with_statement()
        self.assert_fixture_torn_down()
            