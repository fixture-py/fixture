from django.contrib.auth.models import User
from fixture import DataSet, DjangoFixture
from fixture.django_testcase import FixtureTestCase
from datetime import datetime
from fixture.examples.django_example.blog.models import Post, Category
from fixture.examples.django_example.blog.datasets.blog_data import (
                                        django_fixture, UserData, PostData, CategoryData)


class TestBlogRelations(FixtureTestCase):
    fixture = django_fixture
    datasets = [PostData]
    
    def test_data_loaded(self):
        self.assertEquals(Post.objects.all().count(), 3,
                          "There are 3 blog posts")
        post = Post.objects.get(title='3rd test post')
        self.assertEquals(post.categories.count(), 2,
                          "The 3rd test post is in 2 categories")

    def test_reverse_relations(self):
        py = Category.objects.get(title='python')
        self.assertEquals(py.post_set.count(), 3,
                          "There are 3 posts in python category")

    def test_published_for_author(self):
        ben = User.objects.get(username='ben')
        self.assertEquals(ben.post_set.all().count(), 3,
                          "Ben has published 3 posts")
        

__test__ = {'DOCTEST' :
"""
>>> from django.test import Client
>>> from fixture.style import NamedDataStyle
>>> from fixture.examples.django_example.blog.models import Post, Category
>>> from django.core.urlresolvers import reverse
>>> client = Client()
>>> data = DjangoFixture(style=NamedDataStyle()).data(PostData)
>>> data.setup()
>>> sorted(Post.objects.all(), key=lambda r:r.title)
[<Post: 1st test post>, <Post: 2nd test post>, <Post: 3rd test post>]
>>> data.teardown()

"""
}

