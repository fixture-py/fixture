
.. _using-fixture-with-django:

-----------------------------------
Using Fixture To Test Django Models
-----------------------------------

A more extended example of a simple Django app and show how to write a test to load data into its database with fixture.

:ref:`Back to the loadable fixture documentation <using-loadable-fixture>`

We'll be using a simple django project and application (found in fixture/test/test_loadable/test_django/project/). The models.py is included here for reference:

.. _django-models:

    .. literalinclude:: ../../fixture/test/test_loadable/test_django/project/app/models.py
        :language: python
        :linenos:

.. currentmodule:: fixture.loadable.django_loadable

Given the above models and the following fixtures:

    >>> from fixture import DataSet
    >>> class app__Author(DataSet):
    ...    class frank_herbert:
    ...        first_name = "Frank"
    ...        last_name = "Herbert"
    ...    class guido:
    ...        first_name = "Guido"
    ...        last_name = "Van rossum"
    ...        
    >>> class app__Book(DataSet):
    ...    class dune:
    ...        title = "Dune"
    ...        author = app__Author.frank_herbert
    ...    
    ...    class python:
    ...        title = 'Python'
    ...        author = app__Author.guido
    ...        
    >>> class app__Reviewer(DataSet):
    ...    class ben:
    ...        name = 'ben'
    ...        reviewed = [app__Book.dune, app__Book.python]
    
We can do the following:

    >>> from fixture import DjangoFixture
    >>> from django.db.models.loading import get_model, get_app
    >>> from fixture.test.test_loadable.test_django.util import assert_empty
    >>> app = get_app('app')
    >>> assert_empty(app)
    >>> Book = get_model('app', 'Book')
    >>> django_fixture = DjangoFixture()
    >>> data = django_fixture.data(app__Book)
    >>> data.setup()
    
    All the books are here:
    
    >>> Book.objects.all()
    [<Book: Dune, Frank Herbert>, <Book: Python, Guido Van rossum>]
    
    And fixture has pulled in all the Authors too:
    
    >>> Author = get_model('app', 'Author')
    >>> Author.objects.all()
    [<Author: Frank Herbert>, <Author: Guido Van rossum>]
    
    But not the Reviewers:
    
    >>> get_model('app', 'Reviewer').objects.count()
    0
    
    If we load the app__Reviewers DataSet, all of the others will be pulled in:
    >>> data.teardown() # Get rid of the old data
    >>> assert_empty(app)
    
    
    >>> data = django_fixture.data(app__Reviewer)
    >>> data.setup()
    >>> get_model('app', 'Reviewer').objects.count()
    1
    >>> Book.objects.count()
    2
    >>> Author.objects.count()
    2
    >>> data.teardown()


