
import nose
from nose.tools import raises, eq_
from nose.exc import SkipTest
import unittest
from fixture import DataSet
from fixture.loadable import LoadableFixture, EnvLoadableFixture
from fixture.test import env_supports, PrudentTestResult
from fixture import TempIO

def exec_if_supported(code, globals={}, locals={}):
    # seems that for using from __future__ exec needs to think it's compiling a 
    # module
    tmp = TempIO()
    try:
        try:
            mod = compile(code, tmp.join("code.py"), 'exec')
        except SyntaxError:
            raise SkipTest
        else:
            eval(mod, globals, locals)
    finally:
        del tmp


class LoadableTest(object):
    """tests the behavior of fixture.loadable.LoadableFixture object.
    
    to test combinations of loaders and datasets, mix this into a TestCase.
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
    
    def test_with_data_as_d(self):
        """test with: fixture.data() as d"""
        # if not env_supports.with_statement:
        #     raise SkipTest
        
        c = """
from __future__ import with_statement
with self.fixture.data(*self.datasets()) as d:
    self.assert_data_loaded(d)

"""
        exec_if_supported(c, globals(), locals())
        self.assert_data_torndown()

class HavingCategoryData:
    """mixin that adds data to a LoadableTest."""
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
    """mixin that adds data to a LoadableTest."""
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
    """mixin that adds data to a LoadableTest."""
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
        
class HavingReferencedOfferProduct:  
    """mixin that adds data to a LoadableTest."""
    def datasets(self):
        """returns some datasets."""
        
        class CategoryData(DataSet):
            class cars:
                name = 'cars'
            class free_stuff:
                name = 'get free stuff'
        
        class ProductData(DataSet):
            class truck:
                name = 'truck'
                category_id = CategoryData.cars.ref('id')
        
        class OfferData(DataSet):
            class free_truck:
                name = "it's a free truck"
                product_id = ProductData.truck.ref('id')
                category_id = CategoryData.free_stuff.ref('id')
                
        return [ProductData, OfferData]
        
class HavingRefInheritedOfferProduct:  
    """mixin that adds data to a LoadableTest."""
    def datasets(self):
        """returns some datasets."""
        
        class CategoryData(DataSet):
            class cars:
                name = 'cars'
            class free_stuff:
                name = 'get free stuff'
        
        class ProductData(DataSet):
            class truck:
                name = 'truck'
                category_id = CategoryData.cars.ref('id')
        
        class OfferData(DataSet):
            class free_truck:
                name = "it's a free truck"
                product_id = ProductData.truck.ref('id')
                category_id = CategoryData.free_stuff.ref('id')
            class free_spaceship(free_truck):
                id = 99
                name = "it's a free spaceship"
            class free_tv(free_spaceship):
                name = "it's a free TV"
                
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

class TestEnvLoadableFixture(object):
    @raises(ValueError)
    def test_storable_object_cannot_equal_dataset(self):
        class SomeEnvLoadableFixture(EnvLoadableFixture):    
            def rollback(self): pass
            def commit(self): pass
            
        class MyDataSet(DataSet):
            class some_row:
                some_column = 'foo'
                
        efixture = SomeEnvLoadableFixture(env={'MyDataSet': MyDataSet})
        data = efixture.data(MyDataSet)
        data.setup()
        