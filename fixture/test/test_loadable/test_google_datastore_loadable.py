
import sys
import os
from nose.exc import SkipTest
from nose.tools import eq_
import unittest
from fixture import DataSet, TempIO, GoogleDatastoreFixture
from fixture.util import reset_log_level
from fixture.test import conf, attr

tmp = TempIO()

def setup():
    # for prying eyes: NoseGAE http://code.google.com/p/nose-gae/ does this better
    groot = "/usr/local/google_appengine"
    if os.path.exists(groot):
        sys.path.append(groot)
        sys.path.append(os.path.join(groot, "lib/django"))
        sys.path.append(os.path.join(groot, "lib/webob"))
        sys.path.append(os.path.join(groot, "lib/yaml/lib"))
        import google.appengine
        import webob
        import yaml
        import django
        
        from google.appengine.tools import dev_appserver
        
        appid = "<fixture>"
        dev_appserver.SetupStubs(appid, 
                clear_datastore = False, # just removes the files when True
                datastore_path = tmp.join("datastore.data"), 
                history_path = tmp.join("history.data"), 
                login_url = None)
    else:
        raise SkipTest

def teardown():
    # dev_appserver messes with the root logger...
    reset_log_level()

def clear_datastore():
    for basename in ("datastore.data", "history.data"):
        if os.path.exists(tmp.join(basename)):
            os.unlink(tmp.join(basename))

class TestSetupTeardown(unittest.TestCase):
    
    class CategoryData(DataSet):
        class cars:
            name = 'cars'
        class free_stuff:
            name = 'get free stuff'
            
    def setUp(self):
        from google.appengine.ext import db
        
        class Category(db.Model):
            name = db.StringProperty()        
        self.Category = Category
                        
        self.fixture = GoogleDatastoreFixture(env={'CategoryData': self.Category})
    
    def tearDown(self):
        clear_datastore()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        
        eq_(list(self.Category.all()), [])
        
        data = self.fixture.data(self.CategoryData)
        data.setup()
        
        cats = self.Category.all().order('name')
        
        eq_(cats[0].name, 'cars')
        eq_(cats[1].name, 'get free stuff')
        
        data.teardown()
        
        eq_(list(self.Category.all()), [])


class TestRelationships(unittest.TestCase):
            
    def setUp(self):
        from google.appengine.ext import db
        
        class CategoryData(DataSet):
            class red:
                color = 'red'
    
        class ProductData(DataSet):
            class red_truck:
                category = CategoryData.red
                sale_tag = "Big, Shiny Red Truck"
        self.ProductData = ProductData
        
        class Category(db.Model):
            color = db.StringProperty()
        self.Category = Category
        
        class Product(db.Model):
            category = db.ReferenceProperty(Category)
            sale_tag = db.StringProperty()
        self.Product = Product
                        
        self.fixture = GoogleDatastoreFixture(env={
            'CategoryData': self.Category,
            'ProductData': self.Product,
        })
    
    def tearDown(self):
        clear_datastore()
    
    @attr(functional=1)
    def test_setup_then_teardown(self):
        
        eq_(list(self.Category.all()), [])
        eq_(list(self.Product.all()), [])
        
        data = self.fixture.data(self.ProductData)
        data.setup()
        
        products = self.Product.all()
        
        eq_(products[0].sale_tag, "Big, Shiny Red Truck")
        eq_(products[0].category.color, "red")
        
        data.teardown()
        
        eq_(list(self.Category.all()), [])
        eq_(list(self.Product.all()), [])
        
