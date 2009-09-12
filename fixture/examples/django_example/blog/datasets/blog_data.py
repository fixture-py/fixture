from fixture import DataSet, DjangoFixture
from fixture.style import NamedDataStyle
from blog.datasets.user_data import UserData

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
        body            = "this one's about python"
        author          = UserData.ben
        categories      = [CategoryData.python]
        
    class second_post(first_post):
        title           = "2nd test post"
        body            = "this one's also about python"
        
    class third_post(first_post):
        title           = "3rd test post"
        body            = "this one's about both"
        categories      = [CategoryData.python, CategoryData.testing]

django_fixture = DjangoFixture(style=NamedDataStyle())