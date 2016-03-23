from datetime import datetime

from fixture import DataSet


class UserData(DataSet):

    class Meta:
        django_model = 'auth.User'

    class ben:
        first_name = 'Ben'
        last_name = 'Ford'
        username = 'ben'
        email = 'ben@ben.com'
        password = 'sha1$3f491$e891eaf8c62bfcd37ee2b70cea0b2491941fd134'
        is_staff = True
        is_active = True
        is_superuser = True
        date_joined = datetime(2009, 3, 5)
