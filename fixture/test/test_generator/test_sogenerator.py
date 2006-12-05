
import os
import testtools
from nose.tools import eq_
from nose.exc import SkipTest
from testtools.fixtures import affix
from fixture.generator import FixtureGenerator, run_generator
from fixture.test.test_generator import compile_
try:
    import sqlobject
except ImportError:
    sqlobject = None

sqlhub = None
realconn = None
memconn = None

FxtCategory = None
FxtProduct = None
FxtOffer = None

def setup():
    global memconn, realconn, sqlhub, FxtCategory, FxtProduct, FxtOffer
    if not sqlobject:
        raise SkipTest
    from sqlobject import connectionForURI, sqlhub
    from data.sodata import FxtCategory, FxtProduct, FxtOffer
    
    realconn = connectionForURI(os.environ['FIXTURE_TEST_DSN_PG'])
    
    sqlhub.processConnection = realconn
    FxtCategory.createTable()
    FxtProduct.createTable()
    FxtOffer.createTable()
    
    # yes, I've been working in marketing too long ...
    parkas = FxtCategory(name="parkas")
    jersey = FxtProduct(name="jersey", category=parkas)
    rebates = FxtCategory(name="rebates")
    super_cashback = FxtOffer(  name="super cash back!", 
                                product=jersey, category=rebates)
    sqlhub.processConnection = None
    
    # now get the loading db as a sqlite mem connection :
    memconn = connectionForURI("sqlite:/:memory:")
    FxtCategory.createTable(connection=memconn)
    FxtProduct.createTable(connection=memconn)
    FxtOffer.createTable(connection=memconn)

def teardown():
    FxtCategory.dropTable(connection=realconn, cascade=True)
    FxtProduct.dropTable(connection=realconn, cascade=True)
    FxtOffer.dropTable(connection=realconn, cascade=True)

def test_query():
    
    # sanity check :
    assert FxtProduct.select(connection=realconn).count()
    assert not FxtProduct.select(connection=memconn).count()
    
    # generate code w/ data from realconn :
    code = run_generator([  'fixture.test.test_generator.data.sodata.FxtOffer', 
                            '-q', "name = 'super cash back!'",
                            "--dsn", str(os.environ['FIXTURE_TEST_DSN_PG'])])
    print code
    e = compile_(code)
    FxtCategoryData = e['FxtCategoryData']
    FxtProductData = e['FxtProductData']
    FxtOfferData = e['FxtOfferData']
    
    # another sanity check, wipe out the source data
    FxtOffer.clearTable(connection=realconn)
    FxtProduct.clearTable(connection=realconn)
    FxtCategory.clearTable(connection=realconn)
    
    # set our conn back to memory then load the fixture.
    # hmm, seems hoky
    sqlhub.processConnection = memconn
    fxt = affix(FxtCategoryData(), FxtProductData(), FxtOfferData())
    
    rs =  FxtCategory.select()
    eq_(rs.count(), 2)
    parkas = rs[0]
    rebates = rs[1]
    eq_(parkas.name, "parkas")
    eq_(rebates.name, "rebates")
    
    rs = FxtProduct.select()
    eq_(rs.count(), 1)
    eq_(rs[0].name, "jersey")
    
    rs = FxtOffer.select()
    eq_(rs.count(), 1)
    eq_(rs[0].name, "super cash back!")
    
    # note that here we test that colliding fixture key links 
    # got resolved correctly :
    eq_(FxtCategory.get(fxt.fxt_product_1.category_id),   parkas)
    eq_(FxtCategory.get(fxt.fxt_offer_1.category_id),     rebates)
    