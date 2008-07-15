
from addressbook.model import meta, Person
from addressbook.datasets import PersonData
from addressbook.tests import dbfixture
from addressbook.tests import *
from fixture.util import start_debug

class TestBookController(TestController):
    
    def setUp(self):
        super(TestBookController, self).setUp()
        self.data = dbfixture.data(PersonData)
        self.data.setup()
    
    def tearDown(self):
        self.data.teardown()
        super(TestBookController, self).tearDown()

    def test_index(self):
        response = self.app.get(url_for(controller='book'))
        print response
        assert False
