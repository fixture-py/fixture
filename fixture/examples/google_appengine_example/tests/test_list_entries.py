
import unittest
from fixture import GoogleDatastoreFixture, DataSet
from fixture.style import NamedDataStyle
from gblog import application, models
from webtest import TestApp
from datasets import CommentData, EntryData

datafixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())

class TestListEntries(unittest.TestCase):
    def setUp(self):
        self.app = TestApp(application)
        self.data = datafixture.data(CommentData, EntryData)
        self.data.setup()
    
    def tearDown(self):
        self.data.teardown()
    
    def test_entries(self):
        response = self.app.get("/")
        print response
        
        assert EntryData.great_monday.title in response
        assert EntryData.great_monday.body in response
        
        assert CommentData.monday_liked_it.comment in response
        assert CommentData.monday_sucked.comment in response