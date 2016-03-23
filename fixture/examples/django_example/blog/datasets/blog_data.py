from blog.datasets.user_data import UserData

from fixture import DataSet


class CategoryData(DataSet):
    class Meta:
        django_model = 'blog.Category'

    class python:
        title = 'python'
        slug = 'py'

    class testing:
        title = 'testing'
        slug = 'test'


class PostData(DataSet):
    class Meta:
        django_model = 'blog.Post'

    class first_post:
        title = "1st test post"
        body = "this one's about python"
        author = UserData.ben
        categories = [CategoryData.python]

    class second_post(first_post):
        title = "2nd test post"
        body = "this one's also about python"

    class third_post(first_post):
        title = "3rd test post"
        body = "this one's about both"
        categories = [CategoryData.python, CategoryData.testing]
