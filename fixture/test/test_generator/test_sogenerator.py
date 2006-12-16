
import os
import testtools
from nose.tools import eq_
from nose.exc import SkipTest
from testtools.fixtures import affix
from fixture.generator import FixtureGenerator, run_generator
from fixture.test.test_generator import compile_
from fixture.test import env_supports
from fixture.examples.db.sqlobject_examples import (
                    F_Category, F_Product, F_Offer, setup_db, teardown_db)

sqlhub = None
realconn = None
memconn = None

def setup():
    global memconn, realconn, sqlhub
    if not env_supports.sqlobject:
        raise SkipTest
    if not os.environ.get('FIXTURE_TEST_DSN_PG'):
        raise SkipTest
    from sqlobject import connectionForURI, sqlhub
    
    realconn = connectionForURI(os.environ['FIXTURE_TEST_DSN_PG'])
    
    setup_db(realconn)
    
    sqlhub.processConnection = realconn
    # yes, I've been working in marketing too long ...
    parkas = F_Category(name="parkas")
    jersey = F_Product(name="jersey", category=parkas)
    rebates = F_Category(name="rebates")
    super_cashback = F_Offer(  name="super cash back!", 
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
    assert F_Product.select(connection=realconn).count()
    assert not F_Product.select(connection=memconn).count()
    
    # generate code w/ data from realconn :
    code = run_generator([  'fixture.examples.db.sqlobject_examples.F_Offer', 
                            '-q', "name = 'super cash back!'",
                            "--dsn", str(os.environ['FIXTURE_TEST_DSN_PG'])])
    print code
    e = compile_(code)
    F_CategoryData = e['F_CategoryData']
    F_ProductData = e['F_ProductData']
    F_OfferData = e['F_OfferData']
    
    # another sanity check, wipe out the source data
    F_Offer.clearTable(connection=realconn)
    F_Product.clearTable(connection=realconn)
    F_Category.clearTable(connection=realconn)
    
    # set our conn back to memory then load the fixture.
    # hmm, seems hoky
    sqlhub.processConnection = memconn
    fxt = affix(F_CategoryData(), F_ProductData(), F_OfferData())
    
    rs =  F_Category.select()
    eq_(rs.count(), 2)
    parkas = rs[0]
    rebates = rs[1]
    eq_(parkas.name, "parkas")
    eq_(rebates.name, "rebates")
    
    rs = F_Product.select()
    eq_(rs.count(), 1)
    eq_(rs[0].name, "jersey")
    
    rs = F_Offer.select()
    eq_(rs.count(), 1)
    eq_(rs[0].name, "super cash back!")
    
    # note that here we test that colliding fixture key links 
    # got resolved correctly :
    eq_(F_Category.get(fxt.f_product_1.category_id),   parkas)
    eq_(F_Category.get(fxt.f_offer_1.category_id),     rebates)
    