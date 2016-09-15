from fixture import DataSet, NamedDataStyle
from fixture import TempIO
from fixture.loadable import (
    LoadableFixture, EnvLoadableFixture, DBLoadableFixture)
from fixture.test import attr, PrudentTestResult
from nose.exc import SkipTest
from nose.tools import raises, eq_


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
        inspector = self
        class ns:
            tested = False
        
        class SomeDataTestCase(DataTestCase, unittest.TestCase):
            fixture = inspector.fixture
            datasets = inspector.datasets()
            def test_data_test(self):
                ns.tested = True
                inspector.assert_data_loaded(self.data)
        
        res = PrudentTestResult()
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(SomeDataTestCase)
        suite(res)
        
        eq_(res.failures, [])
        eq_(res.errors, [])
        eq_(res.testsRun, 1)
        eq_(ns.tested, True)
        
        inspector.assert_data_torndown()
    
    def test_with_data(self):
        import nose

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
        
        ## FIXME: replace all instances of 
        ## foo_id with foo ... that is, we need refs to data sets
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
                category = CategoryData.cars
        
        class OfferData(DataSet):
            class free_truck:
                name = "it's a free truck"
                product = ProductData.truck
                category = CategoryData.free_stuff
                
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
                category = CategoryData.cars
        
        class OfferData(DataSet):
            class free_truck:
                name = "it's a free truck"
                product = ProductData.truck
                category = CategoryData.free_stuff
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
        
class StubLoadableFixture(DBLoadableFixture):
    def create_transaction(self):
        class NoTrans:
            def commit(self): pass
        return NoTrans()

class MockStorageMedium(DBLoadableFixture.StorageMediumAdapter):
    def save(self, row, column_vals):                
        obj = self.medium()
        for k,v in column_vals:
            setattr(obj, k, v)
        obj.save()
        return obj

class TestDBLoadableRowReferences(object):
    @attr(unit=True)
    def test_row_column_refs_are_resolved(self):
        calls = []
        class MockDataObject(object):
            def save(self):
                calls.append((self.__class__, 'save'))
        class Person(MockDataObject):
            name = None
        class Pet(MockDataObject):
            owner_name = None
        class PersonData(DataSet):
            class bob:
                name = "Bob B. Chillingsworth"
        class PetData(DataSet):
            class fido:
                owner_name = PersonData.bob.ref('name')
            
        ldr = StubLoadableFixture(
            style=NamedDataStyle(), medium=MockStorageMedium, env=locals())
        ldr.begin()
        ldr.load_dataset(PetData())
        
        eq_(calls[0], (Person, 'save'))
        eq_(calls[1], (Pet, 'save'))
        
        bob_db_obj = \
            ldr.loaded[PersonData].meta._stored_objects.get_object('bob')
        eq_(bob_db_obj.name, PersonData.bob.name)
        fido_db_obj = \
            ldr.loaded[PetData].meta._stored_objects.get_object('fido')
        eq_(fido_db_obj.owner_name, PersonData.bob.name)
        
    @attr(unit=True)
    def test_row_refs_are_resolved(self):
        calls = []
        class MockDataObject(object):
            def save(self):
                calls.append((self.__class__, 'save'))
        class Person(MockDataObject):
            name = None
        class Pet(MockDataObject):
            owner = None
        class PersonData(DataSet):
            class bob:
                name = "Bob B. Chillingsworth"
        class PetData(DataSet):
            class fido:
                owner = PersonData.bob
            
        ldr = StubLoadableFixture(
            style=NamedDataStyle(), medium=MockStorageMedium, env=locals())
        ldr.begin()
        ldr.load_dataset(PetData())
        
        eq_(calls[0], (Person, 'save'))
        eq_(calls[1], (Pet, 'save'))
        
        bob_db_obj = \
            ldr.loaded[PersonData].meta._stored_objects.get_object('bob')
        eq_(bob_db_obj.name, PersonData.bob.name)
        fido_db_obj = \
            ldr.loaded[PetData].meta._stored_objects.get_object('fido')
        eq_(fido_db_obj.owner, bob_db_obj)
        
    @attr(unit=True)
    def test_lists_of_row_refs_are_resolved(self):
        calls = []
        class MockDataObject(object):
            def save(self):
                calls.append((self.__class__, 'save'))
        class Person(MockDataObject):
            name = None
        class Pet(MockDataObject):
            owners = None
        class PersonData(DataSet):
            class bob:
                name = "Bob B. Chillingsworth"
            class stacy:
                name = "Stacy Chillingsworth"
        class PetData(DataSet):
            class fido:
                owners = [PersonData.bob, PersonData.stacy]
            
        ldr = StubLoadableFixture(
            style=NamedDataStyle(), medium=MockStorageMedium, env=locals())
        ldr.begin()
        ldr.load_dataset(PetData())
        
        eq_(calls[0], (Person, 'save'))
        eq_(calls[1], (Person, 'save'))
        eq_(calls[2], (Pet, 'save'))
        
        bob_db_obj = \
            ldr.loaded[PersonData].meta._stored_objects.get_object('bob')
        stacy_db_obj = \
            ldr.loaded[PersonData].meta._stored_objects.get_object('stacy')
        fido_db_obj = \
            ldr.loaded[PetData].meta._stored_objects.get_object('fido')
        eq_(fido_db_obj.owners, [bob_db_obj, stacy_db_obj])
        
    @attr(unit=True)
    def test_DataSet_cannot_ref_self(self):
        class MockDataObject(object):
            def save(self): 
                pass
        class Person(MockDataObject):
            name = None
            def __repr__(self):
                return "<Person %s>" % self.name
        class PersonData(DataSet):
            class bob:
                name = "Bob B. Chillingsworth"
                friend = None
            class jenny:
                name = "Jenny Ginetti"
            jenny.friend = bob
            
        ldr = StubLoadableFixture(
            style=NamedDataStyle(), medium=MockStorageMedium, env=locals())
        ldr.begin()
        # was raising load error because the object was getting stored :
        ldr.load_dataset(PersonData())
        
        bob_db_obj = \
            ldr.loaded[PersonData].meta._stored_objects.get_object('bob')
        jenny_db_obj = \
            ldr.loaded[PersonData].meta._stored_objects.get_object('jenny')
        eq_(jenny_db_obj.friend, bob_db_obj)