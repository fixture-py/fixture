
.. _django-doctests:

-----------------------------------
Old django doctests
-----------------------------------

Back to :ref:`using-fixture-with-django`

We'll be using a simple django project and application (found in fixture/test/test_loadable/test_django/project/). The models.py is included here for reference:

.. _doctest-models:

    .. literalinclude:: ../../fixture/test/test_loadable/test_django/project/app/models.py
        :language: python
        :linenos:

.. currentmodule:: fixture.loadable.django_loadable

Given the above models and the following fixtures:

.. doctest::

    >>> from fixture import DataSet
    >>> class AuthorData(DataSet):
    ...    class Meta:
    ...        django_model = 'app.Author'
    ...    class frank_herbert:
    ...        first_name = "Frank"
    ...        last_name = "Herbert"
    ...    class guido:
    ...        first_name = "Guido"
    ...        last_name = "Van rossum"
    ...        
    >>> class BookData(DataSet):
    ...    class Meta:
    ...        django_model = 'app.Book'
    ...    class dune:
    ...        title = "Dune"
    ...        author = AuthorData.frank_herbert
    ...    
    ...    class python:
    ...        title = 'Python'
    ...        author = AuthorData.guido
    ...        
    >>> class ReviewerData(DataSet):
    ...    class Meta:
    ...        django_model = 'app.Reviewer'
    ...    class ben:
    ...        name = 'ben'
    ...        reviewed = [BookData.dune, BookData.python]
    
We can do the following:

.. doctest::

    >>> from fixture import DjangoFixture
    >>> from django.db.models.loading import get_model, get_app
    >>> from fixture.test.test_loadable.test_django.util import assert_empty
    >>> app = get_app('app')
    >>> assert_empty(app)
    >>> Book = get_model('app', 'Book')
    >>> django_fixture = DjangoFixture()
    >>> data = django_fixture.data(BookData)
    >>> data.setup()
    
    All the books are here:
    
.. doctest::

    >>> [(b.title, b.author.first_name) for b in Book.objects.all()]
    [(u'Dune', u'Frank'), (u'Python', u'Guido')]
    
    And fixture has pulled in all the Authors too:
    
.. doctest::

    >>> Author = get_model('app', 'Author')
    >>> [a.first_name for a in Author.objects.all()]
    [u'Frank', u'Guido']
    
    But not the Reviewers:
    
.. doctest::

    >>> get_model('app', 'Reviewer').objects.count()
    0
    
    If we load the ReviewerDatas DataSet, all of the others will be pulled in:
    
.. doctest::

    >>> data.teardown() # Get rid of the old data
    >>> assert_empty(app)
    
    
.. doctest::

    >>> data = django_fixture.data(ReviewerData)
    >>> data.setup()
    >>> get_model('app', 'Reviewer').objects.count()
    1
    >>> Book.objects.count()
    2
    >>> Author.objects.count()
    2
    >>> data.teardown()


