from fixture import DataSet, DjangoFixture
from fixture.loadable.django_loadable import field_is_required
from datetime import datetime
from project.blog.models import Post
from project.blog.fixtures import *


fixture = DjangoFixture()
data = fixture.data(blog__Post)

def setup():
    data.setup()
    
def teardown():
    data.teardown()
    
    
def test_loaded():
    assert Post.objects.filter(status=2).count() == 2
    
"""
>>> from django.test import Client
>>> from project.blog.models import Post, Category
>>> import datetime
>>> from django.core.urlresolvers import reverse
>>> import interlude
>>> interlude.interact(locals())

"""

