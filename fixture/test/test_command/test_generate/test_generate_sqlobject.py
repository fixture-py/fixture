
import os
import testtools
from nose.tools import eq_
from nose.exc import SkipTest
from testtools.fixtures import affix
from fixture.command.generate import FixtureGenerator, run_generator
from fixture.test.test_command.test_generate import compile_
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
    
    realconn = connectionForURI(conf.POSTGRES_DSN)
    memconn = connectionForURI("sqlite:/:memory:")

class GenerateTest(object):
    """tests that a fixture code generator can run with the specified arguments 
    and produce a loadable fixture.
    
    the details of which arguments, how that fixture loads data, and how the 
    data load is proven is defined in the concrete implementation of this test 
    class
    
    """
    args = []
    
    def assert_env_is_clean(self):
        raise NotImplementedError
    
    def assert_env_generated_ok(self, env):
        raise NotImplementedError
        
    def assert_data_loaded(self, data):
        raise NotImplementedError
    
    def load_env(self, module):
        raise NotImplementedError
    
    def run_generator(self, extra_args=[]):
        args = [a for a in self.args]
        if extra_args:
            args.extend(extra_args)
        
        self.assert_env_is_clean()
        code = run_generator(args)
        try:
            e = compile_(code)
            self.assert_env_generated_ok(e)
            data = self.load_env(e)
            self.assert_data_loaded(data)
        except:
            print code
            raise

class SQLObjectGenerateTest(GenerateTest):
    args = [
        "fixture.examples.db.sqlobject_examples.Offer", 
        "--dsn", str(conf.POSTGRES_DSN) ]
    
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
    
    def test_query(self):
        self.run_generator(['-q', "name = 'super cash back!'"])

class UsingTesttoolsTemplate(object):
    def __init__(self, *a,**kw):
        super(UsingTesttoolsTemplate, self).__init__(*a,**kw)
        self.args = [a for a in self.args] + ["--template=testtools"]
    
    def load_datasets(self, module, datasets):
        fxt = affix(*[d() for d in datasets])
        return fxt    
        
class UsingFixtureTemplate(object):
    def __init__(self, *a,**kw):
        super(UsingFixtureTemplate, self).__init__(*a,**kw)
        self.args = [a for a in self.args] + ["--template=fixture"]
    
    def load_datasets(self, module, datasets):
        module['fixture'].loader.connection = memconn
        d = module['fixture'].data(*datasets)
        d.setup()
        return d
        
class TestSQLObjectTesttools(UsingTesttoolsTemplate, SQLObjectGenerateTest):
    pass
    
class TestSQLObjectFixture(UsingFixtureTemplate, SQLObjectGenerateTest):
    pass
    
    