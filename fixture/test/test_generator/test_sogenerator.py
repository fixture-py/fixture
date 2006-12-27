
import os
import testtools
from nose.tools import eq_
from nose.exc import SkipTest
from testtools.fixtures import affix
from fixture.generator import FixtureGenerator, run_generator
from fixture.test.test_generator import compile_
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
    
    setup_db(realconn)
    
    sqlhub.processConnection = realconn
    # yes, I've been working in marketing too long ...
    parkas = Category(name="parkas")
    jersey = Product(name="jersey", category=parkas)
    rebates = Category(name="rebates")
    super_cashback = Offer(  name="super cash back!", 
                                product=jersey, category=rebates)
    sqlhub.processConnection = None
    
    # now get the loading db as a sqlite mem connection :
    memconn = connectionForURI("sqlite:/:memory:")
    setup_db(memconn)

def teardown():
    teardown_db(realconn)
    teardown_db(memconn)

def test_query():
    
    # sanity check :
    assert Product.select(connection=realconn).count()
    assert not Product.select(connection=memconn).count()
    
    # generate code w/ data from realconn :
    code = run_generator([  'fixture.examples.db.sqlobject_examples.Offer', 
                            '-q', "name = 'super cash back!'",
                            "--dsn", str(conf.POSTGRES_DSN)])
    # print code
    e = compile_(code)
    CategoryData = e['CategoryData']
    ProductData = e['ProductData']
    OfferData = e['OfferData']
    
    # another sanity check, wipe out the source data
    Offer.clearTable(connection=realconn)
    Product.clearTable(connection=realconn)
    Category.clearTable(connection=realconn)
    
    # set our conn back to memory then load the fixture.
    # hmm, seems hoky
    sqlhub.processConnection = memconn
    fxt = affix(CategoryData(), ProductData(), OfferData())
    
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
    