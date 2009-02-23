from nose.tools import raises, assert_raises, assert_equal
from fixture.loadable.django_loadable import DjangoEnv
from project.app.models import Book

def test_get_model_from_env():
    assert_equal(Book, DjangoEnv.get('app__Book'))

@raises(ValueError) 
def test_unsplittable_name():
    DjangoEnv.get('app_Book')
    
def test_invalid_app_returns_none():
    assert_equal(None, DjangoEnv.get('no_such_app__Book'))
    
def test_invalid_model_returns_none():
    assert_equal(None, DjangoEnv.get('app__NoSuchModel'))