import django
from django.conf import settings
from django.db import transaction
from django.db.models import connection
from django.test import testcases
from fixture import DjangoFixture


if django.VERSION[:2] < (1, 3):
    check_supports_transactions = lambda conn: conn.creation._rollback_works()
else:
    def check_supports_transactions(conn):
        conn.features.confirm()
        return conn.features.supports_transactions

    
class FixtureTestCase(testcases.TransactionTestCase):
    """Overrides django's fixture setup and teardown code to use DataSets.
    
    Starts a transaction at the begining of a test and rolls it back at the
    end.
    
    See :ref:`Using Fixture With Django <using-fixture-with-django>` for a complete example.
    """

    def _fixture_setup(self):
        """Finds a list called :attr:`datasets` and loads them

        This is done in a transaction if possible.
        I'm not using the settings.DATABASE_SUPPORTS_TRANSACTIONS as I don't
        wnat to assume that :meth:`connection.create_test_db` might not have been
        called
        """
        if check_supports_transactions(connection):
            transaction.enter_transaction_management()
            transaction.managed(True)
            testcases.disable_transaction_methods()
    
        from django.contrib.sites.models import Site
        Site.objects.clear_cache()
        
        if not hasattr(self, 'fixture'):
            self.fixture = DjangoFixture()
        if hasattr(self, 'datasets'):
            self.data = self.fixture.data(*self.datasets)
            self.data.setup()
    
    def _fixture_teardown(self):
        """Finds an attribute called :attr:`data` and runs teardown on it

        (data is created by :meth:`_fixture_setup`)
        """
        if hasattr(self, 'data'):
            self.data.teardown()

        if check_supports_transactions(connection):
            testcases.restore_transaction_methods()
            transaction.rollback()
            transaction.leave_transaction_management()
            connection.close()
