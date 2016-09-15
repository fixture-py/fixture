from app.models import Author, Book, Reviewer
from fixture import DjangoFixture
from fixture.test.test_loadable.test_django.util import assert_empty
from fixture.test.test_loadable.test_django.fixtures import DjangoDataSetWithMeta, AuthorData, BookData, ReviewerData


dj_fixture = DjangoFixture()


def test_fk_rels():
    assert_empty('app')
    try:
        data = dj_fixture.data(AuthorData, BookData)
        data.setup()
        assert Author.objects.get(first_name='Frank').books.count() == 1
    finally:
        data.teardown()
    assert_empty('app')


def test_m2m():
    assert_empty('app')
    try:
        data = dj_fixture.data(AuthorData, BookData, ReviewerData)
        data.setup()
        ben = Reviewer.objects.all()[0]
        # Reviewed have been added as a list
        assert ben.reviewed.count() == 2
        dune = Book.objects.get(title='Dune')
        # Reverse relations work
        assert ben in dune.reviewers.all()
        # A single object passed to a many to many also works
        frank = Author.objects.get(first_name='Frank')
        assert frank.books.count() == 1
        assert dune in frank.books.all()
    finally:
        data.teardown()
    assert_empty('app')


def test_dataset_with_meta():
    assert_empty('app')
    try:
        data = dj_fixture.data(DjangoDataSetWithMeta)
        data.setup()
        assert Author.objects.count() == 2
    finally:
        data.teardown()
    assert_empty('app')
