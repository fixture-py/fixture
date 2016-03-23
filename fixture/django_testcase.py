from django.test.testcases import TestCase

from fixture import DjangoFixture


class FixtureTestCase(TestCase):

    """Overrides django's fixture setup and teardown code to use DataSets.

    See :ref:`Using Fixture With Django <using-fixture-with-django>` for a complete example.
    """

    @classmethod
    def setUpTestData(cls):
        fixture = DjangoFixture()
        data = fixture.data(*cls.datasets)
        data.setup()
