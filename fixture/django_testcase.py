from django.test.testcases import TestCase

from fixture import DjangoFixture


class FixtureTestCase(TestCase):
    """
    Overrides django's fixture setup and teardown code to use DataSets.

    See :ref:`Using Fixture With Django <using-fixture-with-django>` for a
    complete example.

    """

    @classmethod
    def setUpTestData(cls):
        super(FixtureTestCase, cls).setUpTestData()
        fixture = DjangoFixture()
        cls.data = fixture.data(*cls.datasets)
        cls.data.setup()

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown()
        super(FixtureTestCase, cls).tearDownClass()
