
from fixture import DataSet, DjangoFixture
from fixture.style import NamedDataStyle
from fixture.django_testcase import FixtureTestCase
from datetime import datetime
from django.contrib.auth.models import User
from fixture.examples.django_example.blog.models import Post, Category
from fixture.examples.django_example.blog.datasets.blog_data import (
                                        UserData, PostData, CategoryData)

db_fixture = DjangoFixture(style=NamedDataStyle())

class TestBlogWithData(FixtureTestCase):
    fixture = db_fixture
    datasets = [PostData]
    
    def test_blog_posts(self):
        self.assertEquals(Post.objects.all().count(), 3,
                          "There are 3 blog posts")
        post = Post.objects.get(title=PostData.third_post.title)
        self.assertEquals(post.categories.count(), 2,
                          "The 3rd test post is in 2 categories")

    def test_posts_by_category(self):
        py = Category.objects.get(title=CategoryData.python.title)
        self.assertEquals(py.post_set.count(), 3,
                          "There are 3 posts in python category")

    def test_posts_by_author(self):
        ben = User.objects.get(username=UserData.ben.username)
        self.assertEquals(ben.post_set.all().count(), 3,
                          "Ben has published 3 posts")
        



