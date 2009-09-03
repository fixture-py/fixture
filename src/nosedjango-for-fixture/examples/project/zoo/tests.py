from django.test import TestCase
from project.zoo.models import Zoo

class TestDjango(TestCase):
    def testcase1(self):
        zoo = Zoo.objects.create(name='blah')
        assert Zoo.objects.count() == 1

    def testcase2(self):
        zoo = Zoo.objects.create(name='blah')
        assert Zoo.objects.count() == 1

