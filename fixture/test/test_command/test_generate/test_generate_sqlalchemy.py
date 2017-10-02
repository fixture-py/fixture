
import sys
from nose.tools import eq_, raises
from nose.exc import SkipTest

from fixture import DataSet
from fixture.dataset import MergedSuperSet
from fixture.style import NamedDataStyle
from fixture.command.generate import DataSetGenerator
from fixture.command.generate.template import Template
from fixture.command.generate.generate_sqlalchemy import *

from fixture.test import conf, attr
from fixture.test import env_supports
from fixture.test.test_command.test_generate import (
            GenerateTest, UsingTesttoolsTemplate, UsingFixtureTemplate)
from fixture.examples.db import sqlalchemy_examples
from fixture.examples.db.sqlalchemy_examples import (
            metadata, Category, Product, Offer, categories, products, offers )

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

class TestHandlerRecognition(object):
    def setUp(self):
        class options:
            dsn = conf.LITE_DSN
            env = ['fixture.examples.db.sqlalchemy_examples']
        self.generator = DataSetGenerator(options, template=StubTemplate())
        
    def tearDown(self):
        from sqlalchemy.orm import clear_mappers
        clear_mappers()
        
    @attr(unit=True)
    def test_recognizes_mapped_class(self):
        from sqlalchemy.orm import mapper
        mapper(MappableObject, categories)
        hnd = self.generator.get_handler(
                "%s.MappableObject" % (MappableObject.__module__),
                obj=MappableObject)
        eq_(type(hnd), SQLAlchemyMappedClassHandler)
        
    @attr(unit=True)
    def test_recognizes_session_mapper(self):
        from sqlalchemy.orm import mapper, sessionmaker, scoped_session
        
        ScopedSession = scoped_session(sessionmaker(autoflush=False, transactional=False))
        ScopedSession.mapper(MappableObject, categories)
        
        hnd = self.generator.get_handler(
                "%s.MappableObject" % (MappableObject.__module__),
                obj=MappableObject)
        eq_(type(hnd), SQLAlchemySessionMapperHandler)
        
    @attr(unit=True)
    @raises(NotImplementedError)
    def test_recognizes_table_object(self):
        hnd = self.generator.get_handler(
                "%s.categories" % (sqlalchemy_examples.__name__),
                obj=categories)
        eq_(type(hnd), SQLAlchemyTableHandler)
        

class HandlerQueryTest(object):
    class CategoryData(DataSet):
        class bumpy:
            name='bumpy'
        class curvy:
            name='curvy'
        class jagged:
            name='jagged'
    
    @attr(unit=True, generate=True)
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
    
    @attr(unit=True, generate=True)
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
        assert self.data.CategoryData.bumpy.name in names
        assert self.data.CategoryData.curvy.name in names
        assert self.data.CategoryData.jagged.name in names
    
    @attr(unit=True, generate=True)
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

class TestQueryMappedClass(HandlerQueryTest):
    
    def setUp(self):
        from fixture import SQLAlchemyFixture, NamedDataStyle
        import sqlalchemy
        from sqlalchemy.orm import mapper, relation, clear_mappers
        from sqlalchemy import create_engine
        
        metadata.bind = create_engine(conf.LITE_DSN)
        metadata.create_all()
                
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
        
        self.fixture = SQLAlchemyFixture(
                            env=sqlalchemy_examples, 
                            style=NamedDataStyle(),
                            engine=metadata.bind)
        self.data = self.fixture.data(self.CategoryData)
        self.data.setup()
        
        self.hnd = self.generator.get_handler(
                            "%s.Category" % (Category.__module__),
                            obj=Category,
                            connection=metadata.bind)
        self.hnd.begin()
        
    def tearDown(self):
        from sqlalchemy.orm import clear_mappers
        self.data.teardown()
        metadata.drop_all()
        clear_mappers()
        
class TestQuerySessionMappedClass(HandlerQueryTest):
    
    def setUp(self):
        from fixture import SQLAlchemyFixture, NamedDataStyle
        import sqlalchemy
        from sqlalchemy.orm import (
                mapper, relation, clear_mappers, sessionmaker, scoped_session)
        from sqlalchemy import create_engine
        
        metadata.bind = create_engine(conf.LITE_DSN)
        metadata.create_all()
                
        class options:
            dsn = conf.LITE_DSN
            env = ['fixture.examples.db.sqlalchemy_examples']
        self.options = options
        self.generator = DataSetGenerator(self.options, template=StubTemplate())
        
        ScopedSession = scoped_session(sessionmaker(autoflush=False, transactional=True))
        
        ScopedSession.mapper(Category, categories, save_on_init=False)
        ScopedSession.mapper(Product, products, properties={
            'category': relation(Category),
        }, save_on_init=False)
        ScopedSession.mapper(Offer, offers, properties={
            'category': relation(Category, backref='products'),
            'product': relation(Product)
        }, save_on_init=False)
        
        self.fixture = SQLAlchemyFixture(
                            env=sqlalchemy_examples, 
                            style=NamedDataStyle(),
                            engine=metadata.bind)
        self.data = self.fixture.data(self.CategoryData)
        self.data.setup()
        
        self.hnd = self.generator.get_handler(
                            "%s.Category" % (Category.__module__),
                            obj=Category,
                            connection=metadata.bind)
        self.hnd.begin()
        
    def tearDown(self):
        from sqlalchemy.orm import clear_mappers
        self.data.teardown()
        metadata.drop_all()
        clear_mappers()
    
# class TestSQLAlchemyTableHandler(HandlerQueryTest):
#     handler_path = "%s.categories" % (sqlalchemy_examples.__name__) 

class TestSQLAlchemyGenerate(UsingFixtureTemplate, GenerateTest):
    args = [
        "fixture.examples.db.sqlalchemy_examples.Offer", 
        "--dsn", str(conf.HEAVY_DSN),
        "--connect", "fixture.examples.db.sqlalchemy_examples:connect",
        "--setup", "fixture.examples.db.sqlalchemy_examples:setup_mappers"]
    
    def setUp(self):
        global realmeta, RealSession, memmeta, MemSession
        import sqlalchemy
        from sqlalchemy import MetaData, create_engine
        from sqlalchemy.orm import clear_mappers, scoped_session, sessionmaker, relation
        clear_mappers()
        
        realmeta = MetaData(bind=create_engine(conf.HEAVY_DSN))
        RealSession = scoped_session(sessionmaker(autoflush=False, transactional=False, bind=realmeta.bind))
        
        memmeta = MetaData(bind=create_engine(conf.LITE_DSN))
        MemSession = scoped_session(sessionmaker(autoflush=True, transactional=False, bind=memmeta.bind))
        
        self.setup_mappers()
        
        session = RealSession()
        
        # data source :
        categories.create(bind=realmeta.bind)
        products.create(bind=realmeta.bind)
        offers.create(bind=realmeta.bind)
        
        parkas = Category()
        parkas.name = "parkas"
        session.save(parkas)
        jersey = Product()
        jersey.name = "jersey"
        jersey.category = parkas
        session.save(jersey)
        
        rebates = Category()
        rebates.name = "rebates"
        rebates.id = 2
        super_cashback = Offer()
        super_cashback.name = "super cash back!"
        super_cashback.product = jersey
        super_cashback.category = rebates
        session.save(super_cashback)
        session.save(rebates)
        
        session.flush()
        
        # data target:
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
            
    def assert_data_loaded(self, fxt):
        session = MemSession()
        session.clear()
        
        rs = session.query(Category).order_by('name').all()
        eq_(len(rs), 2)
        parkas = rs[0]
        rebates = rs[1]
        eq_(parkas.name, "parkas")
        eq_(rebates.name, "rebates")
        
        rs = session.query(Product).all()
        eq_(len(rs), 1)
        eq_(rs[0].name, "jersey")
        
        rs = session.query(Offer).all()
        eq_(len(rs), 1)
        eq_(rs[0].name, "super cash back!")
        
        # note that here we test that colliding fixture key links 
        # got resolved correctly :
        eq_(session.query(Category).filter_by(id=fxt.products_1.category_id).one(), parkas)
        eq_(session.query(Category).filter_by(id=fxt.offers_1.category_id).one(), rebates)
    
    def assert_env_is_clean(self):
        # sanity check, ensure source has data :
        session = RealSession()
        session.clear()
        assert session.query(Product).count()
        
        # ensure target is empty :
        session = MemSession()
        session.clear()
        eq_(session.query(Product).count(), 0)
        
        ### FIXME, this shouldn't be so lame
        # clear mappers so that the dataset_generator() can setup mappers on its own:
        from sqlalchemy.orm import clear_mappers
        clear_mappers()
    
    def assert_env_generated_ok(self, e):
        # get rid of the source so that we
        # are sure we aren't ever querying the source db
        engine = realmeta.bind
        # offers.drop(bind=engine)
        # products.drop(bind=engine)
        # categories.drop(bind=engine)
    
    def create_fixture(self):
        return SQLAlchemyFixture(
            env = self.env,
            style = NamedDataStyle(),
            dataclass = MergedSuperSet,
            # *load* data into the memory db :
            engine = memmeta.bind
        )
    
    def load_env(self, env):
        data = self.load_datasets(env, 
                [env['categoriesData'], env['productsData'], env['offersData']])
        return data
    
    def setup_mappers(self):
        from sqlalchemy.orm import mapper, relation
        mapper(Category, categories)
        mapper(Product, products, properties={
            'category': relation(Category)
        })
        mapper(Offer, offers, properties={
            'category': relation(Category),
            'product': relation(Product)
        })
        
    def visit_loader(self, loader):
        loader.engine = memmeta.bind
        