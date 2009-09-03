from nose.tools import raises, assert_raises, assert_equal
from fixture.loadable.django_loadable import DjangoEnv, DjangoFixture
from fixture.examples.django_example.app.models import Book
from fixture import DataSet
from fixture.style import NamedDataStyle

@raises(ValueError) 
def test_unsplittable_name():
    DjangoEnv.get('app_Book')
    
def test_invalid_app_returns_none():
    assert_equal(None, DjangoEnv.get('no_such_app__Book'))
    
def test_invalid_model_returns_none():
    assert_equal(None, DjangoEnv.get('app__NoSuchModel'))

def test_model_lookup_by_qualified_model_name():
    
    class SomeDataset(DataSet):
        class Meta:
            django_model = "app.Book"
        class foo:
            foo = 1
    
    fixture = DjangoFixture()
    ds = SomeDataset()
    fixture.attach_storage_medium(ds)
    assert_equal(ds.meta.storage_medium.medium, Book)

def test_model_lookup_by_explicit_app_label_and_name():
    
    class SomeDataset(DataSet):
        class Meta:
            django_app_label = "app"
            storable_name = "Book"
        class foo:
            foo = 1
    
    fixture = DjangoFixture()
    ds = SomeDataset()
    fixture.attach_storage_medium(ds)
    assert_equal(ds.meta.storage_medium.medium, Book)

def test_model_lookup_by_app_label_and_style_derived_name():
    
    class BookData(DataSet):
        class Meta:
            django_app_label = "app"
        class foo:
            foo = 1
    
    fixture = DjangoFixture(style=NamedDataStyle())
    ds = BookData()
    fixture.attach_storage_medium(ds)
    assert_equal(ds.meta.storage_medium.medium, Book)

@raises(ValueError)
def test_dataset_with_malformed_model_name():
    
    class SomeDataset(DataSet):
        class Meta:
            django_model = "not_dot_separated_model_name"
        class foo:
            foo = 1
    
    fixture = DjangoFixture()
    ds = SomeDataset()
    fixture.attach_storage_medium(ds)

@raises(ValueError)
def test_dataset_without_resolvable_model_name():
    
    class UnknownData(DataSet):
        class foo:
            foo = 1
    
    fixture = DjangoFixture()
    ds = UnknownData()
    fixture.attach_storage_medium(ds)

