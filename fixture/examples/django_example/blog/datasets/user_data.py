from fixture import DataSet, DjangoFixture
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