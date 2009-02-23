from fixture import DjangoFixture, DataSet, style
from fixture.exc import LoadError
from nose.tools import raises, assert_raises

from project.app import models

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
    assert 'reviewers' in models.Book._meta.get_all_field_names()
    data = dj_fixture.data(BookData)
    assert_raises(LoadError, data.setup)
    data.teardown()
        

