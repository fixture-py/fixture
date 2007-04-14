
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
realcontext = None
memmeta = None
memcontext = None

def setup():
    if not env_supports.sqlalchemy:
        raise SkipTest

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
        from sqlalchemy import BoundMetaData
        from sqlalchemy.ext.sessioncontext import SessionContext
        
        self.meta = BoundMetaData(conf.LITE_DSN)
        self.connection = self.meta.engine.connect()
        self.ctx = SessionContext(
                lambda: sqlalchemy.create_session(bind_to=self.connection))
                
        class options:
            dsn = conf.LITE_DSN
            env = ['fixture.examples.db.sqlalchemy_examples']
        self.options = options
        self.generator = DataSetGenerator(self.options, template=StubTemplate())
            
        setup_db(self.meta, self.ctx)
    
    def tearDown(self):
        teardown_db(self.meta, self.ctx)

class TestSQLAlchemyHandler(SQLAlchemyHandlerTest):
    @attr(unit=True)
    def test_recognizes_assigned_mapper(self):
        hnd = self.generator.get_handler("%s.Category" % (Category.__module__))
        assert isinstance(hnd, SQLAlchemyAssignedMapperHandler)
    
    @attr(unit=True)
    def test_recognizes_mapped_class(self):
        from sqlalchemy import mapper
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
        
        from fixture import SQLAlchemyFixture
        from fixture.style import NamedDataStyle
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

class TestSQLAlchemyAssignedMapperHandler(SQLAlchemyHandlerQueryTest):
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
        import sqlalchemy
        from sqlalchemy import BoundMetaData
        from sqlalchemy.ext.sessioncontext import SessionContext
        
        global realmeta, realcontext, memmeta, memcontext
        realmeta = BoundMetaData(conf.HEAVY_DSN)
        realcontext = SessionContext(
                lambda: sqlalchemy.create_session(bind_to=realmeta.engine))
            
        memmeta = BoundMetaData(conf.LITE_DSN)
        memcontext = SessionContext(
                lambda: sqlalchemy.create_session(bind_to=memmeta.engine))
            
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
        # realcontext.current.clear()
        
        teardown_db(memmeta, memcontext)
        # memcontext.current.clear()

class TestGenerateSQLAlchemyFixture(
        UsingFixtureTemplate, SQLAlchemyGenerateTest):        
    def visit_loader(self, loader):
        loader.meta = memmeta
        loader.session_context = memcontext
        