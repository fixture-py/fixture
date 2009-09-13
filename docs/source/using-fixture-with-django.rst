
.. _using-fixture-with-django:

=====================================
Using Fixture To Test Django
=====================================

.. contents:: :local:

The `Django's ORM <http://www.djangoproject.com>`_ already has its own `data loading mechanism`_ for testing but you can use the Fixture module as an alternative.  When using Fixture, you don't have to deal with JSON or XML, you simply create :class:`DataSet <fixture.dataset.DataSet>` objects in Python code and load them with an instance of :class:`DjangoFixture <fixture.loadable.django_loadable.DjangoFixture>`.  Using Python code helps you share objects and common field definitions whereas in Django you might have many JSON files with the same field definitions in separate places.  Using Python code also allows you to represent test data alongside your test code, take advantage of inheritance, and improve readability.

However, unlike Django, Fixture does not currently provide a way to auto generate DataSet classes from a real database.  It is safe to mix Fixture style data loading and Django style data loading if desired.

This feature was contributed by `Ben Ford <http://twitter.com/boothead>`_.

.. note:: Fixture can only be used with `Django version 1.0.2 <http://www.djangoproject.com/download/>`_ and greater.

.. _django-models:

Example Django application
---------------------------

Here's a simple blog application written in Django.  The data model consists of Post objects that belong to Category objects.

    .. literalinclude:: ../../fixture/examples/django_example/blog/models.py
        :language: python

.. currentmodule:: fixture.loadable.django_loadable

.. note::
    
    A complete version of this blog app with fixtures and tests can be found in fixture/examples/django_example/blog/

.. _django-fixtures:

Defining datasets
-----------------

To load data into the test database, you first create some :class:`DataSet <fixture.dataset.DataSet>` subclasses in Python code:

.. code-block:: python

    class UserData(DataSet):
        class Meta:
            django_model = 'auth.User'
        class ben:
            first_name = 'Ben'
            last_name = 'Ford'
            # ...

In this example, the nested class ``ben`` will be used to create a row in django's ``auth.User`` model.  Fixture knows to load into that model because of the ``django_model`` attribute of the inner :class:`Meta <fixture.dataset.DataSetMeta>` class.  A couple other ways to link each DataSet to a specfic Django model are shown later on.

Defining relationships between models
--------------------------------------

More realistically you would need to load one or more foreign key dependencies as part of each DataSet.  Here are the DataSets for testing the blog application, taken from ``fixture/examples/django_example/blog/datasets/blog_data.py`` 

.. literalinclude:: ../../fixture/examples/django_example/blog/datasets/blog_data.py
    :language: python

Here ``first_post`` is a blog entry posted in the Python category and authored by Ben (notice the UserData class has been imported from the user_data module).

In this style, each DataSet class name starts with that of the Django model it should be loaded into and a shared class BlogMeta has the attribute ``django_app_label='blog'`` to tell the loader which app to find models in.

.. note:: 
    In the current release of fixture you can only specify a relationship from the direction that the field is defined, *not* from the reverse (see :class:`DjangoMedium <fixture.loadable.django_loadable.DjangoMedium>` for more details). 
    
Loading some data
------------------
    

.. doctest::
    :hide:
    
    >>> import os
    >>> os.environ['DJANGO_SETTINGS_MODULE'] = 'fixture.examples.django_example.settings'
    >>> from django.core.management import call_command
    >>> call_command('syncdb', interactive=False)
    >>> call_command('reset', 'blog', interactive=False)
    ...
    >>> from fixture.examples.django_example.blog.datasets.blog_data import CategoryData, PostData
    >>> from fixture.examples.django_example.blog.models import Post
    
To load these records programatically you'd use a :class:`DjangoFixture <fixture.loadable.django_loadable.DjangoFixture>` instance and a :class:`NamedDataStyle <fixture.style.NamedDataStyle>` instance:
    
.. doctest::
    
    >>> from fixture import DjangoFixture
    >>> from fixture.style import NamedDataStyle
    >>> db_fixture = DjangoFixture(style=NamedDataStyle())

You would insert each defined row into its target database table via setup() :
    
.. doctest::

    >>> data = db_fixture.data(CategoryData, PostData)
    >>> data.setup()
    >>> Post.objects.filter(author__first_name='Ben').count()
    3
    >>> data.teardown()
    >>> Post.objects.all()
    []

Foreign DataSet classes like UserData need not be mentioned in data() since they are loaded automatically when referenced.
    
Loading data in a test
-----------------------

Here is an example of how to create a unittest style class to test with data.  This is taken directly from ``fixture.examples.django_example.blog.tests``:

.. literalinclude:: ../../fixture/examples/django_example/blog/tests.py
    :language: python

.. note:: This test case uses Django's fast data loading strategy introduced in 1.1 whereby data is removed by rolling back the transaction.  If you need to test specific transactional behavior in your code then don't use this test case.

See :class:`fixture.django_testcase.FixtureTestCase` for details on how to configure the test case.

For further reading, check the API docs for :mod:`fixture.django_testcase` and :mod:`fixture.loadable.django_loadable`

.. _data loading mechanism: http://docs.djangoproject.com/en/dev/topics/testing/
.. _django's testing framework: http://docs.djangoproject.com/en/dev/topics/testing/