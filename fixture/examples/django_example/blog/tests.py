from django.contrib.auth.models import User
from fixture import DataSet, DjangoFixture
from fixture.django_testcase import FixtureTestCase
from datetime import datetime
from fixture.examples.django_example.blog.models import Post, Category
from fixture.examples.django_example.blog.fixtures import django_fixture, UserData, PostData, CategoryData


class TestBlogRelations(FixtureTestCase):
    fixture = django_fixture
    datasets = [PostData]
    
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
>>> from fixture.style import NamedDataStyle
>>> from fixture.examples.django_example.blog.models import Post, Category
>>> from django.core.urlresolvers import reverse
>>> client = Client()
>>> data = DjangoFixture(style=NamedDataStyle()).data(PostData)
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

