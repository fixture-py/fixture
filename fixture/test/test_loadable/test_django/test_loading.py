
from fixture import DjangoFixture
from fixture import DataSet, style

from project.app import models
from fixtures import *
from util import *

dj_fixture = DjangoFixture()
    
def test_fk_rels():
    assert_empty(models)
    data = dj_fixture.data(AuthorData, BookData)
    try:
        data.setup()
        assert models.Author.objects.get(first_name='Frank').books.count() == 1
    finally:
        data.teardown()
    assert_empty(models)
    
def test_m2m():
    assert_empty(models)
    data = dj_fixture.data(AuthorData, BookData, ReviewerData)
    try:
        data.setup()
        ben = models.Reviewer.objects.all()[0]
        # Reviewed have been added as a list
        assert ben.reviewed.count() == 2
        dune = models.Book.objects.get(title='Dune')
        # Reverse relations work
        assert ben in dune.reviewers.all()
        # A single object passed to a many to many also works
        frank = models.Author.objects.get(first_name='Frank')
        assert frank.books.count() == 1
        assert dune in frank.books.all()
    finally:
        data.teardown()
    assert_empty(models)

def test_dataset_with_meta():
    assert_empty(models)
    data = dj_fixture.data(DjangoDataSetWithMeta)
    try:
        data.setup()
        assert models.Author.objects.count() == 2
    finally:
        data.teardown()
    assert_empty(models)
    