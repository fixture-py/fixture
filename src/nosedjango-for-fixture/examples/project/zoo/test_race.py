# We have two test classes because we want to induce a race condition
# and ensure that the database is always reset between test methods

from zoo.models import *

class TestDBRace1(object):
    def setup(self):
        assert Zoo.objects.count() == 0

    def test1(self):
        obj = Zoo.objects.create(name='sample1')
        assert Zoo.objects.count() == 1
        assert Zoo.objects.all()[0].name == 'sample1'


class TestDBRace2(object):
    def setup(self):
        assert Zoo.objects.count() == 0

    def test1(self):
        obj = Zoo.objects.create(name='sample2')
        assert Zoo.objects.count() == 1
        assert Zoo.objects.all()[0].name == 'sample2'
