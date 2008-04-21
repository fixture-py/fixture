
import sys
from nose.tools import eq_, raises
from nose.exc import SkipTest

from fixture import DataSet
from fixture.command.generate import DataSetGenerator
from fixture.command.generate.template import Template
from fixture.command.generate.generate_sqlalchemy import *

from fixture.test import conf, attr
from fixture.test import env_supports
from fixture.test.test_command.test_generate import (
            GenerateTest, UsingTesttoolsTemplate, UsingFixtureTemplate)
from fixture.examples.db import sqlalchemy_examples
from fixture.examples.db.sqlalchemy_examples import (
            Category, Product, Offer, setup_db, teardown_db,
            categories, products, offers )

realmeta = None
RealSession = None
memmeta = None
MemSession = None

def setup():
    if not env_supports.sqlalchemy:
        raise SkipTest

@attr(unit=True)
def test_TableEnv():
    from sqlalchemy import Table, MetaData, INT, Column, create_engine
    meta = MetaData(bind=create_engine(conf.LITE_DSN))
    class env(object):
        taxi = Table('taxi', meta, Column('id', INT, primary_key=True))
    somedict = {
        'barbara': Table('barbara', meta, Column('id', INT, primary_key=True))
    }
    
    e = TableEnv('fixture.examples.db.sqlalchemy_examples', env, somedict)
    
    tbl = e[products]
    eq_(tbl['name'], 'products')
    eq_(tbl['module'], sqlalchemy_examples)
    
    tbl = e[env.taxi]
    eq_(tbl['name'], 'taxi')
    eq_(tbl['module'], sys.modules[__name__])
    
    tbl = e[somedict['barbara']]
    eq_(tbl['name'], 'barbara')
    # can't get module from dict...
    eq_(tbl['module'], None)

class MappableObject(object):
    pass

class StubTemplate(Template):
    def add_import(self, _import):
        pass
    def begin(self):
        pass
    def header(self, handler):
        pass
    def render(self, tpl):
        pass

class SQLAlchemyHandlerTest(object):
    def setUp(self):
        import sqlalchemy
        from sqlalchemy.orm import mapper, relation, clear_mappers
        from sqlalchemy import MetaData, create_engine
        
        self.meta = MetaData(bind=create_engine(conf.LITE_DSN))
        self.connection = self.meta.bind.connect()
                
        class options:
            dsn = conf.LITE_DSN
            env = ['fixture.examples.db.sqlalchemy_examples']
        self.options = options
        self.generator = DataSetGenerator(self.options, template=StubTemplate())
        
        mapper(Category, categories)
        mapper(Product, products, properties={
            'category': relation(Category),
        })
        mapper(Offer, offers, properties={
            'category': relation(Category, backref='products'),
            'product': relation(Product)
        })
        # setup_db(self.meta, self.ctx)
    
    def tearDown(self):
        from sqlalchemy.orm import clear_mappers
        # teardown_db(self.meta, self.ctx)
        clear_mappers()

class TestSQLAlchemyHandler(SQLAlchemyHandlerTest):    
    @attr(unit=True)
    def test_recognizes_mapped_class(self):
        from sqlalchemy.orm import mapper
        mapper(MappableObject, categories)
        hnd = self.generator.get_handler(
                "%s.MappableObject" % (MappableObject.__module__))
        assert isinstance(hnd, SQLAlchemyMappedClassHandler)
        
    @attr(unit=True)
    @raises(NotImplementedError)
    def test_recognizes_table_object(self):
        hnd = self.generator.get_handler(
                "%s.categories" % (sqlalchemy_examples.__name__))
        assert isinstance(hnd, SQLAlchemyTableHandler), (
                    "unexpected type: %s" % (type(hnd)))
                    
class TestSQLAlchemyHandler(SQLAlchemyHandlerTest):
    def setUp(self):
        super(TestSQLAlchemyHandler, self).setUp()
        from sqlalchemy.orm import (
                mapper, relation, clear_mappers, sessionmaker, scoped_session)
        clear_mappers()
        
        self.Session = scoped_session(sessionmaker(autoflush=True, transactional=True))
        
        self.Session.mapper(Category, categories)
        self.Session.mapper(Product, products, properties={
            'category': relation(Category),
        })
        self.Session.mapper(Offer, offers, properties={
            'category': relation(Category, backref='products'),
            'product': relation(Product)
        })
    
    def tearDown(self):
        super(TestSQLAlchemyHandler, self).tearDown()
        self.Session.remove()
        
    @attr(unit=True)
    def test_recognizes_session_mapper(self):
        hnd = self.generator.get_handler("%s.Category" % (Category.__module__))
        assert isinstance(hnd, SQLAlchemySessionMapperHandler)

class SQLAlchemyHandlerQueryTest(SQLAlchemyHandlerTest):
    class CategoryData(DataSet):
        class bumpy:
            name='bumpy'
        class curvy:
            name='curvy'
        class jagged:
            name='jagged'
    
    handler_path = None
            
    def setUp(self):
        super(SQLAlchemyHandlerQueryTest, self).setUp()
        
        from fixture import SQLAlchemyFixture, NamedDataStyle
        self.fixture = SQLAlchemyFixture(
                            env=sqlalchemy_examples, 
                            style=NamedDataStyle(),
                            session_context=self.ctx)
        self.data = self.fixture.data(self.CategoryData)
        self.data.setup()
        
        self.hnd = self.generator.get_handler(
                            self.handler_path,
                            connection=self.connection)
        self.hnd.begin()
    
    def tearDown(self):
        self.data.teardown()
        super(SQLAlchemyHandlerQueryTest, self).tearDown()
    
    @attr(unit=True)
    def test_find(self):
        try:
            rs = self.hnd.find(self.data.CategoryData.bumpy.id)
        except:
            self.hnd.rollback()
            raise
        else:
            self.hnd.commit()
        assert rs, "unexpected record set: %s" % rs
        obj = [o for o in rs]
        eq_(obj[0].name, self.data.CategoryData.bumpy.name)
    
    @attr(unit=True)
    def test_findall(self):
        try:
            rs = self.hnd.findall()
        except:
            self.hnd.rollback()
            raise
        else:
            self.hnd.commit()
        assert rs, "unexpected record set: %s" % rs
        names = set([o.name for o in rs])
        print names
        assert self.data.CategoryData.bumpy.name in names
        assert self.data.CategoryData.curvy.name in names
        assert self.data.CategoryData.jagged.name in names
    
    @attr(unit=True)
    def test_findall_accepts_query(self):
        try:
            rs = self.hnd.findall("name='curvy'")
        except:
            self.hnd.rollback()
            raise
        else:
            self.hnd.commit()
        assert rs, "unexpected record set: %s" % rs
        obj = [o for o in rs]
        eq_(len(obj), 1)

class TestSQLAlchemySessionMapperHandler(SQLAlchemyHandlerQueryTest):
    handler_path = "%s.Category" % (Category.__module__)
    
# class TestSQLAlchemyTableHandler(SQLAlchemyHandlerQueryTest):
#     handler_path = "%s.categories" % (sqlalchemy_examples.__name__) 

class SQLAlchemyGenerateTest(GenerateTest):
    args = [
        "fixture.examples.db.sqlalchemy_examples.Offer", 
        "--dsn", str(conf.HEAVY_DSN) ]
    
    def assert_data_loaded(self, fxt):
        session = memcontext.current
        conn = session.bind_to.connect()
        
        rs = [r for r in conn.execute(categories.select())]
        eq_(len(rs), 2)
        parkas = rs[0]
        rebates = rs[1]
        eq_(parkas.name, "parkas")
        eq_(rebates.name, "rebates")
        
        rs = [r for r in conn.execute(products.select())]
        eq_(len(rs), 1)
        eq_(rs[0].name, "jersey")

        rs = [r for r in conn.execute(offers.select())]
        eq_(len(rs), 1)
        eq_(rs[0].name, "super cash back!")
        
        # note that here we test that colliding fixture key links 
        # got resolved correctly :
        def get(table, id):
            c = conn.execute(table.select(table.c.id==id))
            return c.fetchone()
        
        eq_(get(categories, fxt.products_1.category_id), parkas )
        eq_(get(categories, fxt.offers_1.category_id), rebates )
    
    def assert_env_is_clean(self):
        # sanity check :
        session = RealSession()
        assert session.query(Product).count()
        session = MemSession()
        eq_(session.query(Product).count(), 0)
    
    def assert_env_generated_ok(self, e):
        # get rid of the source so that we
        # are sure we aren't ever querying the source db
        engine = realmeta.bind
        e['offers'].drop(connectable=engine)
        e['products'].drop(connectable=engine)
        e['categories'].drop(connectable=engine)
    
    def load_env(self, env):
        data = self.load_datasets(env, 
                [env['categoriesData'], env['productsData'], env['offersData']])
        return data
    
    def setUp(self):
        global realmeta, RealSession, memmeta, MemSession
        import sqlalchemy
        from sqlalchemy import MetaData, create_engine
        from sqlalchemy.orm import clear_mappers, scoped_session, sessionmaker, relation
        clear_mappers()
        
        realmeta = MetaData(bind=create_engine(conf.HEAVY_DSN))
        RealSession = scoped_session(sessionmaker(autoflush=True, transactional=True, bind=realmeta.bind))
        
        RealSession.mapper(Category, categories)
        RealSession.mapper(Product, products, properties={
            'category': relation(Category)
        })
        RealSession.mapper(Offer, offers, properties={
            'category': relation(Category),
            'product': relation(Product)
        })
        # self.tearDown()
        
        categories.create(bind=realmeta.bind)
        products.create(bind=realmeta.bind)
        offers.create(bind=realmeta.bind)
        session = RealSession()
        trans = session.begin()
        
        parkas = Category()
        parkas.name = "parkas"
        session.save(parkas)
        jersey = Product()
        jersey.name = "jersey"
        jersey.category = parkas
        session.save(jersey)
        
        rebates = Category(name="rebates", id=2)
        super_cashback = Offer()
        super_cashback.name = "super cash back!"
        super_cashback.product = jersey
        super_cashback.category = rebates
        session.save(super_cashback)
        session.save(rebates)
        
        # realmeta.bind.echo = 0
        session.flush()
        trans.commit()
        
        # clear_mappers()
        # print list(session.query(Offer).filter("name = 'super cash back!'"))
        
        # from fixture.examples.db.sqlalchemy_examples import Offer
        # from sqlalchemy import MetaData, create_engine
        # from sqlalchemy.orm import scoped_session, sessionmaker
        # realmeta = MetaData(bind=create_engine(conf.HEAVY_DSN))
        # RealSession = scoped_session(sessionmaker(autoflush=True, transactional=True, bind=realmeta.bind))
        # session = RealSession()
        # print list(session.query(Offer).filter("name = 'super cash back!'"))
        
        
        memmeta = MetaData(bind=create_engine(conf.LITE_DSN))
        MemSession = scoped_session(sessionmaker(autoflush=True, transactional=True, bind=memmeta.bind))
        
        categories.create(bind=memmeta.bind)
        products.create(bind=memmeta.bind)
        offers.create(bind=memmeta.bind)
    
    def tearDown(self):
        if realmeta:
            offers.drop(bind=realmeta.bind)
            products.drop(bind=realmeta.bind)
            categories.drop(bind=realmeta.bind)
        if memmeta:
            offers.drop(bind=memmeta.bind)
            products.drop(bind=memmeta.bind)
            categories.drop(bind=memmeta.bind)
        
        # teardown_db(realmeta, realcontext)
        # realcontext.current.clear()
        
        # teardown_db(memmeta, memcontext)
        # memcontext.current.clear()

class TestGenerateSQLAlchemyFixture(
        UsingFixtureTemplate, SQLAlchemyGenerateTest):        
    def visit_loader(self, loader):
        loader.meta = memmeta
        loader.session_context = memcontext
        