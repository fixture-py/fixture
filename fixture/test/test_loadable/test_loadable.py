
import nose
from nose.tools import raises, eq_
from nose.exc import SkipTest
import unittest
from fixture import DataSet, SequencedSet
from fixture.loadable import LoadableFixture
from fixture.test import env_supports, PrudentTestResult


class LoaderTest:
    """tests the behavior of fixture.loadable.LoadableFixture object.
    
    to test combinations of loaders and datasets, implement this base tester.
    """
    fixture = None
    
    def assert_data_loaded(self, dataset):
        """assert that the dataset was loaded."""
        raise NotImplementedError
    
    def assert_data_torndown(self):
        """assert that the dataset was torn down."""
        raise NotImplementedError
        
    def datasets(self):
        """returns some datasets."""
        raise NotImplementedError
    
    def test_DataTestCase(self):
        from fixture import DataTestCase
        import unittest
        driver = self
        class ns:
            tested = False
        
        class SomeDataTestCase(DataTestCase, unittest.TestCase):
            fixture = driver.fixture
            datasets = driver.datasets()
            def test_data_test(self):
                ns.tested = True
                driver.assert_data_loaded(self.data)
        
        class PrudentTestResult(unittest.TestResult):
            """A test result that raises an exception immediately"""
            def _raise_err(self, err):
                exctype, value, tb = err
                raise Exception("%s: %s" % (exctype, value)), None, tb
        
            def addFailure(self, test, err):
                self._raise_err(err)
            def addError(self, test, err):
                self._raise_err(err)
        
        res = PrudentTestResult()
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(SomeDataTestCase)
        suite(res)
        
        eq_(res.failures, [])
        eq_(res.errors, [])
        eq_(res.testsRun, 1)
        eq_(ns.tested, True)
        
        self.assert_data_torndown()
    
    def test_with_data(self):
        """test @fixture.with_data"""
        import nose, unittest
        
        class ns:
            was_setup=False
            was_torndown=False
        def setup():
            ns.was_setup=True
        def teardown():
            ns.was_torndown=True
        
        kw = dict(setup=setup, teardown=teardown)
        @self.fixture.with_data(*self.datasets(), **kw)
        def test_data_test(data):
            eq_(ns.was_setup, True)
            self.assert_data_loaded(data)
        
        case = nose.case.FunctionTestCase(test_data_test)
        res = PrudentTestResult()
        case(res)
        
        eq_(res.failures, [])
        eq_(res.errors, [])
        eq_(res.testsRun, 1)
        
        eq_(ns.was_torndown, True)
        self.assert_data_torndown()
    
    def test_with_data_recovery(self):
        """test @fixture.with_data recovery"""
        @raises(RuntimeError)
        @self.fixture.with_data(*self.datasets())
        def test_exception_tears_down(fxt):
            self.assert_data_loaded(fxt)
            raise RuntimeError
        test_exception_tears_down()
        self.assert_data_torndown()
        
    def test_with_data_generator(self):
        """test @fixture.with_data generator"""
        @self.fixture.with_data(*self.datasets())
        def test_generate_data_tests():
            def test_x(data, x):
                self.assert_data_loaded(data)
            for x in range(2):
                yield test_x, x
        
        # fixme: use nose's interface for running generator tests...
        for stack in test_generate_data_tests():
            stack = list(stack)
            func = stack.pop(0)
            func(*stack) 
        self.assert_data_torndown()
    
    def test_with_data_as_d(self):
        """test with: fixture.data() as d"""
        if not env_supports.with_statement:
            raise SkipTest
        
        c = """    
        with self.fixture.data(*self.datasets()) as d:
            self.assert_data_loaded(d)
        """
        eval(c)
        self.assert_data_torndown()
        
    def test_with_data_as_d_recovery(self):
        """test with: fixture.data() as d recovery"""
        if not env_supports.with_statement:
            raise SkipTest
            
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

class HavingCategoryData:
    """mixin that adds data to a LoaderTest."""
    def datasets(self):
        """returns a single category data set."""
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('gray_stuff', dict(id=1, name='gray')),
                    ('yellow_stuff', dict(id=2, name='yellow')),
                )
        return [CategoryData]

class HavingCategoryAsDataType:
    def datasets(self):
        class CategoryData(DataSet):
            class gray_stuff:
                id = 1
                name = 'gray'
            class yellow_stuff:
                id = 2
                name = 'yellow'
                
        return [CategoryData]
        
class HavingOfferProductData:   
    """mixin that adds data to a LoaderTest."""
    def datasets(self):
        """returns some datasets.""" 
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('cars', dict(id=1, name='cars')),
                    ('free_stuff', dict(id=2, name='get free stuff')),)
        
        class ProductData(DataSet):
            class Meta:
                references = (CategoryData,)
            def data(self):
                return (('truck', dict(
                            id=1, 
                            name='truck', 
                            category_id=self.ref.cars.id)),)
        
        class OfferData(DataSet):
            class Meta:
                references = (CategoryData, ProductData)
            def data(self):
                return (
                    ('free_truck', dict(
                            id=1, 
                            name='free truck',
                            product_id=self.ref.truck.id,
                            category_id=self.ref.free_stuff.id)),
                )
        return [OfferData, ProductData]
        
class HavingOfferProductAsDataType:  
    """mixin that adds data to a LoaderTest."""
    def datasets(self):
        """returns some datasets."""
        
        class CategoryData(DataSet):
            class cars:
                id = 1
                name = 'cars'
            class free_stuff:
                id = 2
                name = 'get free stuff'
        
        class ProductData(DataSet):
            class truck:
                id = 1
                name = 'truck'
                category_id = CategoryData.cars.ref('id')
        
        class OfferData(DataSet):
            class free_truck:
                id = 1
                name = "it's a free truck"
                product_id = ProductData.truck.ref('id')
                category_id = CategoryData.free_stuff.ref('id')
                
        return [ProductData, OfferData]
        
class HavingSequencedOfferProduct:  
    """mixin that adds data to a LoaderTest."""
    def datasets(self):
        """returns some datasets."""
        
        class CategoryData(SequencedSet):
            class cars:
                name = 'cars'
            class free_stuff:
                name = 'get free stuff'
        
        class ProductData(SequencedSet):
            class truck:
                name = 'truck'
                category_id = CategoryData.cars.ref('id')
        
        class OfferData(SequencedSet):
            class free_truck:
                name = "it's a free truck"
                product_id = ProductData.truck.ref('id')
                category_id = CategoryData.free_stuff.ref('id')
                
        return [ProductData, OfferData]
        

class LoaderPartialRecoveryTest(HavingOfferProductData):
    fixture = None
    
    def assert_partial_load_aborted(self):
        """assert that no datasets were loaded."""
        raise NotImplementedError
    
    def partial_datasets(self):
        """returns some real datasets, then some dummy ones."""
        d = [ds for ds in self.datasets()]
        
        class DummyData(DataSet):
            def data(self):
                return (
                    ('nonexistant', dict(shape='green', color='circular')),
                )
        d.append(DummyData)
        return d
    
    def test_with_data_iterruption(self):
        """test @fixture.with_data interruption"""
        @raises(LoadableFixture.StorageMediaNotFound)
        @self.fixture.with_data(*self.partial_datasets())
        def test_partial_datasets(fxt):
            pass
        test_partial_datasets()        
        self.assert_partial_load_aborted()