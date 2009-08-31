
.. _using-fixture-with-django:

=====================================
Using Fixture To Test Django
=====================================

Back to the :ref:`loadable fixture <using-loadable-fixture>` documentation.

Django already has its own `data fixture mechanism`_ but you can still use the Fixture module to manage data needed for a Django test.  When using Fixture, you don't have to deal with JSON or XML, you simply create :class:`DataSet <fixture.dataset.DataSet>` objects in Python code and load them with an instance of :class:`DjangoFixture <fixture.loadable.django_loadable.DjangoFixture>`.  Using Python code helps you share objects and common field definitions where as in Django you might have many JSON files with the same field definitions in separate places.  Using Python code also allows you to represent test data alongside your test code to improve readability.

However, unlike Django, Fixture does not currently provide a way to auto generate (or regenerate) DataSet classes.  It is safe to mix Fixture style data loading and Django style data loading if desired.

.. _example-django-project:
.. _data fixture mechanism: fixme

Example project
---------------

We'll be using a simple django project and application (found in fixture/test/test_loadable/test_django/project/). An excerpt of models.py is shown here for reference:

.. _django-models:

    .. literalinclude:: ../../fixture/test/test_loadable/test_django/project/blog/models.py
        :language: python

.. currentmodule:: fixture.loadable.django_loadable

As with `django's testing framework`_ you can use fixture in doctests or in a unittest style, additionally you can use them within nose.

.. _django-fixtures:

Defining fixtures
-----------------------

Fixture has two different ways to associate :class:`DataSets <fixture.dataset.DataSet>` with django models,
by the making the name of the dataset class being the app and the model separated by a double underscore,
or using the inner :class:`Meta <fixture.dataset.DataSetMeta>` and giving it a :attr:`~fixture.loadable.django_loadable.DjangoFixture.django_model` attribute.
This means that the following two are equivalent ways to define some data to insert into django's user table:

.. code-block:: python

    class auth__User(DataSet):
        class ben:
            first_name = 'Ben'
            last_name = 'Ford'
            username = 'ben'
            # ...

.. code-block:: python

    class UserDataSet(DataSet):
        class Meta:
            django_model = 'auth.User'
        class ben:
            first_name = 'Ben'
            last_name = 'Ford'
            # ...


Relationships between models
---------------------------------

At the moment you can only specify a relationship from the direction that the field is defined *not* from the reverse.
There are plans to fix this, but for a first shot at fixture support in django I wanted to contrain the scope of it a bit.
See :class:`~fixture.loadable.django_loadable.DjangoMedium` for more details about this. Here's how to define a relationship:

This is an extract from the :ref:`example django project <example-django-project>` fixtures.py file.

.. code-block:: python

    class blog__Category(DataSet):
        class python:
            title = 'python'
            slug = 'py'

    class blog__Post(DataSet):
        class first_post:
            title           = "1st test post"
            slug            = '1st'
            body            = "this one's about python"
            status          = 1 # Draft
            allow_comments  = True
            author          = auth__User.ben
            categories      = blog__Category.python

Here ``first_post`` is in the category python defined above and it's author is ben (the auth__User fixture is not included for brevity)


Doctest usage
------------------

Here's an example doctest:

.. testsetup::

    from project.blog.fixtures import *
    from django.test.utils import setup_test_environment
    setup_test_environment()

.. doctest::

    >>> from fixture import DjangoFixture
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from project.blog.models import Post, Category
    >>> client = Client()
    
    Load the data:
    
    >>> data = DjangoFixture().data(blog__Post)
    >>> data.setup()
    
    Model API tests
    
    >>> Post.objects.all()
    [<Post: 3rd test post>, <Post: 2nd test post>, <Post: 1st test post>]
    >>> Post.objects.published()
    [<Post: 3rd test post>, <Post: 2nd test post>]
    
    Using the test client
    
    >>> response = client.get(reverse('blog_index'))
    >>> response.status_code
    200
    >>> response.context[-1]['object_list']
    [<Post: 3rd test post>, <Post: 2nd test post>]
    >>> response = client.get(reverse('blog_category_list'))
    >>> response.status_code
    200
    >>> response.context[-1]['object_list']
    [<Category: python>, <Category: testing>]
    
    Teardown the data
    
    >>> data.teardown()


Unittest usage
------------------

There's a subclass of django TransactionTestCase available which is fixture aware :class:`fixture.django_testcase.FixtureTestCase`. This can be straight swap for existing testcases and will autoload fixtures.
Fixtures are loaded and torn down for each test method, this should be quicker than running the django flush command each time.

Here's how you use it:

.. code-block:: python

    from fixture.django_testcase import FixtureTestCase
    # from path.to.fixtures import *

    class TestBlogRelations(FixtureTestCase):
        datasets = [blog__Post]
        
        def test_data_loaded(self):
            self.assertEquals(Post.objects.filter(status=2).count(), 2,
                              "There are 2 published blog posts")
            post = Post.objects.get(slug='3rd')
            self.assertEquals(post.categories.count(), 2,
                              "The 3rd test post is in 2 categories")
    
        def test_reverse_relations(self):
            py = Category.objects.get(slug='py')
            self.assertEquals(py.post_set.count(), 3,
                              "There are 3 posts in python category")
    
        def test_published_for_author(self):
            ben = User.objects.get(username='ben')
            self.assertEquals(ben.post_set.published().count(), 2,
                              "Ben has published 2 posts")
                              
The :attr:`~fixture.django_testcase.FixtureTestCase.datasets` attribute is a list of datasets that you want available for this set of tests. As with django's json/xml/yaml fixtures, these are loaded into the database in the setup method and then torn down for each test. The :class:`~fixture.django_testcase.FixtureTestCase` also makes use of django's recent transactional test case refactoring [1]_ so it should be pretty fast.

Note in the above example we've only specified *one* dataset to be loaded but from that fixure knows that it needs to go and fetch the categories dataset and the user dataset because they are refered to.

Now consider what happens if you're developing a few related django applications, and the schema for one of them changes. If you're using some dumped fixtures to express your data for testing then you now have to go and manually edit all fixtures that contain this model. If you're building something with some models that a lot of others relate to (for example a Profile object in a social networking site with blog posts, forums posts contacts etc) then you've just made a lot of work for yourself! However if you've developed a fixture for your Profile that you or other developers are importing and relating to when writing fixtures for their own related models, then you only need to change **one** fixture and your data model is up to date again. (The tests might still break, but you'll know that there's a consistent set of data representing cononical Profiles in the database). This for me is the killer feature of declarative fixtures versus a textual representation of the database at some point in time. 

The FixtureTestCase class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: fixture.django_testcase.FixtureTestCase
    :show-inheritance:
    :members: _fixture_setup, _fixture_teardown

    .. attribute:: datasets

        This is a list of :class:`DataSets <fixture.dataset.DataSet>` that will be created and destroyed for each test method.
        The result of setting them up will be referenced by the :attr:`data`

    .. attribute:: data

        Any :attr:`datasets` found are loaded and refereneced here for later teardown


.. _django's testing framework: http://docs.djangoproject.com/en/dev/topics/testing/
.. [1] `Django changeset 9756 <http://code.djangoproject.com/changeset/9756>`_