
import nose
from nose.tools import raises
from nose.exc import SkipTest
import unittest
from fixture import DataSet
from fixture.test import env_supports

__all__ = ['LoaderTest', 'HavingCategoryData', 'HavingOfferProductData']

class LoaderTest:
    """tests the behavior of fixture.loader.Loader object.
    
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
    
    def test_with_data(self):
        """test @fixture.with_data"""
        
        @self.fixture.with_data(*self.datasets())
        def test_data_test(data):
            self.assert_data_loaded(data)
        test_data_test()
        self.assert_data_torndown()
        
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
        
        @raises(RuntimeError)
        @self.fixture.with_data(*self.datasets())
        def test_exception_tears_down(fxt):
            self.assert_data_loaded(fxt)
            raise RuntimeError
        test_exception_tears_down()
        self.assert_data_torndown()
    
    def test_with_data_as_f(self):
        """test with: fixture.data() as d"""
        if not env_supports.with_statement:
            raise SkipTest
        
        c = """    
        with self.fixture.data(*self.datasets()) as d:
            self.assert_data_loaded(d)
        """
        eval(c)
        self.assert_data_torndown()
        
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
        
class HavingOfferProductData:  
    """mixin that adds data to a LoaderTest."""
    def datasets(self):
        """returns some datasets."""
        
        class WidgetData(DataSet):
            def data(self):
                return (('just_some_widget', dict(type='foobar')),)
        
        class CategoryData(DataSet):
            def data(self):
                return (
                    ('cars', dict(id=1, name='cars')),
                    ('free_stuff', dict(id=2, name='get free stuff')),)
        
        class ProductData(DataSet):
            class Config:
                requires = (CategoryData,)
            def data(self):
                return (('truck', dict(
                            id=1, 
                            name='truck', 
                            category_id=self.ref.CategoryData.cars.id)),)
        
        class OfferData(DataSet):
            class Config:
                requires = (CategoryData, ProductData)
                references = (WidgetData,)
            def data(self):
                return (
                    ('free_truck', dict(
                            id=1, 
                            name=('free truck by %s' % 
                                    self.ref.WidgetData.just_some_widget.type),
                            product_id=self.ref.ProductData.truck.id,
                            category_id=self.ref.CategoryData.free_stuff.id)),
                )
        return [OfferData, ProductData]