
from nose.exc import SkipTest
from fixture.test import conf
from fixture.test import env_supports
from fixture.test.test_command.test_generate import GenerateTest
from fixture.examples.db.sqlalchemy_examples import (
            Category, Product, Offer, setup_db, teardown_db)

realmeta = None
realcontext = None
memmeta = None
memcontext = None

def setup():
    if not env_supports.sqlalchemy:
        raise SkipTest
    
    global realmeta, realcontext, memmeta, memcontext
    import sqlalchemy
    from sqlalchemy import BoundMetaData
    from sqlalchemy.ext.sessioncontext import SessionContext
    
    realmeta = BoundMetaData(conf.POSTGRES_DSN)
    realcontext = SessionContext(
            lambda: sqlalchemy.create_session(bind_to=realmeta.engine))
            
    memmeta = BoundMetaData(conf.MEM_DSN)
    memcontext = SessionContext(
            lambda: sqlalchemy.create_session(bind_to=memmeta.engine))

class SqlAlchemyGeberateTest(GenerateTest):
    args = [
        "fixture.examples.db.sqlalchemy_examples.Offer", 
        "--dsn", str(conf.POSTGRES_DSN) ]
    
    def setUp(self):        
        setup_db(realmeta, realcontext)
        
        session = realcontext.current
        
        parkas = Category(name="parkas")
        session.save(parkas)
        jersey = Product(name="jersey", category=parkas)
        session.save(jersey)
        rebates = Category(name="rebates")
        session.save(rebates)
        super_cashback = Offer( name="super cash back!", 
                                product=jersey, category=rebates)
        session.save(super_cashback)
        session.flush()
                                    
        setup_db(memmeta, memcontext, non_primary=True)
    
    def tearDown(self):
        teardown_db(realmeta, realcontext)
        teardown_db(memmeta, memcontext)

class TestSomething(SqlAlchemyGeberateTest):
    def test_something(self):
        pass