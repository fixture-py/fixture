from fixture import DataSet, DjangoFixture
from fixture.django_testcase import FixtureTestCase
from datetime import datetime
from project.blog.models import Post
from project.blog.fixtures import *


#fixture = DjangoFixture()
#data = fixture.data(blog__Post)
#
#def setup():
#    data.setup()
#    
#def teardown():
#    data.teardown()
#    
#    
#def test_loaded():
#    assert Post.objects.filter(status=2).count() == 2

class TestBlogLoading(FixtureTestCase):
    datasets = [blog__Post]
    
    def test_data_loaded(self):
        self.assertEquals(Post.objects.filter(status=2).count(), 2)
    
"""
>>> from django.test import Client
>>> from project.blog.models import Post, Category
>>> import datetime
>>> from django.core.urlresolvers import reverse
>>> import interlude
>>> interlude.interact(locals())

"""

