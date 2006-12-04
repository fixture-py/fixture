
import os
from nose.tools import eq_, raises
import testtools
from testtools.fixtures import affix
from fixture.generator import FixtureGenerator, run_generator
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
    
from sqlobject import connectionForURI, SQLObject, StringCol, ForeignKey, sqlhub
    
class FxtCategory(SQLObject):
    name = StringCol()

class FxtProduct(SQLObject):
    name = StringCol()
    category = ForeignKey('FxtCategory')

class FxtOffer(SQLObject):
    name = StringCol()
    category = ForeignKey('FxtCategory')
    product = ForeignKey('FxtProduct')

realconn = None
memconn = None

def setup():
    global memconn, realconn
    assert os.environ.has_key("FIXTURE_TEST_DSN_PG"), (
            "you need to define a postgres dsn in an environment var named "
            "FIXTURE_TEST_DSN_PG to run this test.  WARNING!  The DB user must "
            "be able to create tables and note that the tables will be deleted "
            "at teardown.")
    
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
    
    # now get the loading db as a sqlite mem connection :
    memconn = connectionForURI("sqlite:/:memory:")
    FxtCategory.createTable(connection=memconn)
    FxtProduct.createTable(connection=memconn)
    FxtOffer.createTable(connection=memconn)

def teardown():
    FxtCategory.dropTable(connection=realconn, cascade=True)
    FxtProduct.dropTable(connection=realconn, cascade=True)
    FxtOffer.dropTable(connection=realconn, cascade=True)

def get_code():
    code = run_generator([  'fixture.test.test_generator.FxtOffer', 
                            '-q', "name = 'super cash back!'"])
    return code

def get_code_old_way():
    """gets code from testools.console.genfix"""
    
    from testtools.console.genfix import SOFixtureGenerator
    
    strout = StringIO()
    generate = SOFixtureGenerator( "P" ) # classes made like P_ClassName
    generate( FxtOffer, query="name = 'super cash back!'", 
                outfile=strout)
    code = strout.getvalue()
    return code

def test_so_generator():
    
    # sanity check :
    assert FxtProduct.select().count()
    assert not FxtProduct.select(connection=memconn).count()
    
    # code = get_code_old_way()
    code = get_code()
    
    # print code
    e = {}
    eval(compile(code, 'stdout', 'exec'), e)
    FxtCategoryData = e['FxtCategoryData']
    FxtProductData = e['FxtProductData']
    FxtOfferData = e['FxtOfferData']
    
    # another sanity check, wipe out the source data
    FxtOffer.clearTable()
    FxtProduct.clearTable()
    FxtCategory.clearTable()
    
    # hmm, set it back to memory then load the fixture :
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
    
    # here was the problem with the old merge code :
    eq_(FxtCategory.get(fxt.fxt_product_1.category_id),   parkas)
    eq_(FxtCategory.get(fxt.fxt_offer_1.category_id),     rebates)
    
@raises(ValueError)
def test_unhandlable_object():
    generate = FixtureGenerator()
    
    class Stranger(object):
        """something that cannot produce data."""
        pass
        
    generate(Stranger())
    