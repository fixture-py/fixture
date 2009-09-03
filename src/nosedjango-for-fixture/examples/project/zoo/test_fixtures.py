from project.zoo.models import *

class TestFixture1(object):
    fixtures = ['f1.json']

    def test_count(self):
        assert Zoo.objects.count() == 1
        assert Zoo.objects.get(id=1).name == 'f1'


class TestFixture2(object):
    fixtures = ['f2.json']
    def test_count(self):
        assert Zoo.objects.count() == 1
        assert Zoo.objects.get(id=1).name == 'f2'
