
import sys
from nose.tools import eq_, raises
from nose.exc import SkipTest
from fixture.test import conf
from fixture.test import env_supports
from fixture.test.test_command.test_generate import (
            GenerateTest, UsingTesttoolsTemplate, UsingFixtureTemplate)
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

class SqlAlchemyGenerateTest(GenerateTest):
    args = [
        "fixture.examples.db.sqlalchemy_examples.Offer", 
        "--dsn", str(conf.POSTGRES_DSN) ]
    
    def assert_env_is_clean(self):
        # sanity check :
        session = realcontext.current
        assert len(session.query(Product).select())
        session = memcontext.current
        eq_(len(session.query(Product).select()), 0)
    
    def assert_env_generated_ok(self, e):
        # get rid of the source so that we
        # are sure we aren't ever querying the source db
        engine = realmeta.engine
        e['offers'].drop(connectable=engine)
        e['products'].drop(connectable=engine)
        e['categories'].drop(connectable=engine)
    
    def load_env(self, env):
        data = self.load_datasets(env, 
                [env['categoriesData'], env['productsData'], env['offersData']])
        return data
    
    def setUp(self):
        setup_db(realmeta, realcontext)
        
        session = realcontext.current
        
        parkas = Category(name="parkas", id=1)
        session.save(parkas)
        rebates = Category(name="rebates", id=2)
        session.save(rebates)
        
        session.flush()
        
        jersey = Product(id=1, name="jersey", category_id=parkas.id)
        session.save(jersey)
        session.flush()
        super_cashback = Offer( name="super cash back!", 
                                product_id=jersey.id, category_id=rebates.id)
        session.save(super_cashback)
        session.flush()
        # realmeta.engine.echo = 0
                                    
        setup_db(memmeta, memcontext, non_primary=True)
    
    def tearDown(self):
        teardown_db(realmeta, realcontext)
        realcontext.current.clear()
        
        teardown_db(memmeta, memcontext)
        memcontext.current.clear()

class TestGenerateSqlAlchemyFixture(
        UsingFixtureTemplate, SqlAlchemyGenerateTest):        
    def visit_loader(self, loader):
        loader.meta = realmeta
        loader.session_context = realcontext
        