from django.contrib.auth.models import User
from fixture import DataSet, DjangoFixture
from fixture.django_testcase import FixtureTestCase
from datetime import datetime
from project.blog.models import Post, Category
from project.blog.fixtures import *


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
        

__test__ = {'DOCTEST' :
"""
>>> #import interlude
>>> #interlude.interact(locals())
>>> from django.test import Client
>>> from project.blog.models import Post, Category
>>> from django.core.urlresolvers import reverse
>>> client = Client()
>>> data = DjangoFixture().data(blog__Post)
>>> data.setup()
>>> Post.objects.all()
[<Post: 3rd test post>, <Post: 2nd test post>, <Post: 1st test post>]
>>> Post.objects.published()
[<Post: 3rd test post>, <Post: 2nd test post>]
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
>>> data.teardown()

"""
}

