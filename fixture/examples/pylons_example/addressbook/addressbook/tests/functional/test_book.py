
from addressbook.model import meta, Person
from addressbook.datasets import PersonData, AddressData
from addressbook.tests import *

class TestBookController(TestController):        

    def setUp(self):
        super(TestBookController, self).setUp()
        self.data = dbfixture.data(PersonData) # AddressData loads implicitly
        self.data.setup()
    
    def tearDown(self):
        self.data.teardown()
        super(TestBookController, self).tearDown()

    def test_index(self):
        response = self.app.get(url_for(controller='book'))
        print response
        assert PersonData.joe_gibbs.name in response
        assert PersonData.joe_gibbs.email in response
        assert AddressData.joe_in_montego.address in response
        assert AddressData.joe_in_ny.address in response