from nose.tools import assert_raises
from util import assert_empty

from fixture import DjangoFixture, DataSet, style
from app import models
from fixture.exc import LoadError


class ReviewerData(DataSet):
    class ben:
        name = 'ben'


class BookData(DataSet):
    class dune:
        title = "Dune"
        reviewers = [ReviewerData.ben]


class AuthorData(DataSet):
    class frank_herbert:
        first_name = "Frank"
        last_name = "Herbert"
        books = BookData.dune


dj_fixture = DjangoFixture(env=models, style=style.NamedDataStyle())


def test_wrong_relation_declaration():
    assert_empty('app')
    assert 'reviewers' in models.Book._meta.get_all_field_names()
    data = dj_fixture.data(BookData)
    assert_raises(LoadError, data.setup)
    data.teardown()
    assert_empty('app')


def test_invalid_m2m():
    class ReviewerData(DataSet):
        class ben:
            name = 'ben'
            reviewed = [BookData.dune, AuthorData.frank_herbert]

    assert_empty('app')
    data = dj_fixture.data(ReviewerData)
    assert_raises(LoadError, data.setup)
    data.teardown()
    assert_empty('app')
