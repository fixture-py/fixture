
import os
from nose.tools import eq_
from nose.exc import SkipTest
from fixture import SQLObjectFixture
from fixture.command.generate import DataSetGenerator, dataset_generator
from fixture.dataset import MergedSuperSet
from fixture.style import NamedDataStyle
from fixture.test.test_command.test_generate import (
        compile_, GenerateTest, UsingTesttoolsTemplate, UsingFixtureTemplate)
from fixture.test import env_supports, conf
from fixture.examples.db.sqlobject_examples import (
                    Category, Product, Offer, setup_db, teardown_db)

sqlhub = None
realconn = None
memconn = None

def setup():
    global memconn, realconn, sqlhub
    if not env_supports.sqlobject:
        raise SkipTest
        
    from sqlobject import connectionForURI, sqlhub
    
    realconn = connectionForURI(conf.HEAVY_DSN)
    memconn = connectionForURI("sqlite:/:memory:")

def teardown():
    realconn.close()
    globals()['realconn'] = None
    memconn.close()
    globals()['memconn'] = None

class SQLObjectGenerateTest(GenerateTest):
    args = [
        "fixture.examples.db.sqlobject_examples.Offer", 
        "--dsn", str(conf.HEAVY_DSN) ]
    
    def assert_data_loaded(self, fxt):
        rs =  Category.select()
        eq_(rs.count(), 2)
        parkas = rs[0]
        rebates = rs[1]
        eq_(parkas.name, "parkas")
        eq_(rebates.name, "rebates")

        rs = Product.select()
        eq_(rs.count(), 1)
        eq_(rs[0].name, "jersey")

        rs = Offer.select()
        eq_(rs.count(), 1)
        eq_(rs[0].name, "super cash back!")

        # note that here we test that colliding fixture key links 
        # got resolved correctly :
        eq_(Category.get(fxt.product_1.category_id),   parkas)
        eq_(Category.get(fxt.offer_1.category_id),     rebates)
    
    def assert_env_is_clean(self):
        # sanity check :
        assert Product.select(connection=realconn).count()
        assert not Product.select(connection=memconn).count()
    
    def assert_env_generated_ok(self, e):
        CategoryData = e['CategoryData']
        ProductData = e['ProductData']
        OfferData = e['OfferData']

        # another sanity check, wipe out the source data
        Offer.clearTable(connection=realconn)
        Product.clearTable(connection=realconn)
        Category.clearTable(connection=realconn)
    
    def create_fixture(self):
        return SQLObjectFixture(
            env = self.env,
            style = NamedDataStyle(),
            dataclass = MergedSuperSet,
        )
    
    def load_datasets(self, module, conn, datasets):
        raise NotImplementedError
    
    def load_env(self, env):
        # set our conn back to memory then load the fixture.
        # hmm, seems hoky
        sqlhub.processConnection = memconn
        data = self.load_datasets(env, 
                    [env['CategoryData'], env['ProductData'], env['OfferData']])
        return data
    
    def setUp(self):        
        setup_db(realconn)
        sqlhub.processConnection = realconn
    
        parkas = Category(name="parkas")
        jersey = Product(name="jersey", category=parkas)
        rebates = Category(name="rebates")
        super_cashback = Offer(  name="super cash back!", 
                                    product=jersey, category=rebates)
        sqlhub.processConnection = None
    
        # now get the loading db as a sqlite mem connection :
        setup_db(memconn)
    
    def tearDown(self):
        sqlhub.processConnection = None
        teardown_db(realconn)
        teardown_db(memconn)
        
class TestSQLObjectTesttools(UsingTesttoolsTemplate, SQLObjectGenerateTest):
    pass
    
class TestSQLObjectFixture(UsingFixtureTemplate, SQLObjectGenerateTest):
    def visit_loader(self, loader):
        loader.connection = memconn
    
    