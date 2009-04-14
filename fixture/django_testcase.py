from django.conf import settings
from django.db import transaction
from django.db.models import connection
from django.test import testcases
from fixture import DjangoFixture


class FixtureTestCase(testcases.TransactionTestCase):
    """Overrides django's fixture setup and teardown code to use DataSets.
    
    Starts a transaction at the begining of a test and rolls it back at the
    end.
    """

    def _fixture_setup(self):
        """Finds an attrubute called 'datasets' and sets it up as a fixture

        This is done in a transaction if possible
        I'm not using the settings.DATABASE_SUPPORTS_TRANSACTIONS as
        create_test_db might not have been called
        """
        if connection.creation._rollback_works():
            print "_rollback_works!"
            transaction.enter_transaction_management()
            transaction.managed(True)
            testcases.disable_transaction_methods()
    
        from django.contrib.sites.models import Site
        Site.objects.clear_cache()
    
        if hasattr(self, 'datasets'):
            print "loading dataset"
            self.data = DjangoFixture().data(*self.datasets)
            self.data.setup()
    
    def _fixture_teardown(self):
        """Finds an attribute called data and runs teardown on it

        (data is created by :meth:`_fixture_setup`)
        """
        if hasattr(self, 'data'):
            self.data.teardown()

        if connection.creation._rollback_works():
            testcases.restore_transaction_methods()
            transaction.rollback()
            transaction.leave_transaction_management()
            connection.close()
