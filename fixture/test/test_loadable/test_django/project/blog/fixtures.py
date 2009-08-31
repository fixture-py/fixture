from fixture import DataSet, DjangoFixture
from fixture.style import NamedDataStyle
from datetime import datetime

class UserData(DataSet):
    class Meta:
        django_app_label = 'auth'
    class ben:
        first_name = 'Ben'
        last_name = 'Ford'
        username = 'ben'
        email = 'ben@ben.com'
        password = 'sha1$3f491$e891eaf8c62bfcd37ee2b70cea0b2491941fd134'
        is_staff = 'True'
        is_active = 'True'
        is_superuser = 'True'
        #last_login = '2009-03-03 12:51:02.086360'
        date_joined = datetime(2009, 03, 05)

class BlogMeta:
    django_app_label = 'blog'
    
class CategoryData(DataSet):
    class Meta(BlogMeta):
        pass
    class python:
        title = 'python'
        slug = 'py'
        
    class testing:
        title = 'testing'
        slug = 'test'

class PostData(DataSet):
    class Meta(BlogMeta):
        pass
    class first_post:
        title           = "1st test post"
        slug            = '1st'
        body            = "this one's about python"
        status          = 1 # Draft
        allow_comments  = True
        author          = UserData.ben
        categories      = CategoryData.python
        
    class second_post(first_post):
        title           = "2nd test post"
        slug            = '2nd'
        body            = "this one's also about python"
        status          = 2 # Public
        
    class third_post(first_post):
        title           = "3rd test post"
        slug            = '3rd'
        body            = "this one's about both"
        status          = 2 # Public
        categories      = [CategoryData.python, CategoryData.testing]

django_fixture = DjangoFixture(style=NamedDataStyle())