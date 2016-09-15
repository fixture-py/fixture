import sys

from fixture.command.generate import dataset_generator
from fixture.test import conf
from nose.exc import SkipTest
from nose.tools import eq_
from six import print_


def setup():
    # every tests needs a real db conn :
    if not conf.HEAVY_DSN:
        raise SkipTest

def compile_(code):
    """compiles code string for a module.
    
    returns dict w/ attributes of that module.
    """
    mod = {}
    eval(compile(code, 'stdout', 'exec'), mod)
    return mod

class GenerateTest(object):
    """tests that a fixture code generator can run with the specified arguments 
    and produce a loadable fixture.
    
    the details of which arguments, how that fixture loads data, and how the 
    data load is proven is defined in the concrete implementation of this test 
    class
    
    """
    args = []
    
    def __init__(self, *a, **kw):
        super(GenerateTest, self).__init__(*a, **kw)
        self.env = None
    
    def assert_env_is_clean(self):
        raise NotImplementedError
    
    def assert_env_generated_ok(self, env):
        raise NotImplementedError
        
    def assert_data_loaded(self, data):
        raise NotImplementedError
    
    def create_fixture(self):
        raise NotImplementedError("must return a concrete LoadableFixture instance, i.e. SQLAlchemyFixture")
    
    def load_env(self, module):
        raise NotImplementedError
    
    def dataset_generator(self, extra_args=[]):
        args = [a for a in self.args]
        if extra_args:
            args.extend(extra_args)
        
        self.assert_env_is_clean()
        code = dataset_generator(args)
        try:
            self.env = compile_(code)
            self.assert_env_generated_ok(self.env)
            data = self.load_env(self.env)
            self.assert_data_loaded(data)
        except:
            print_(code)
            raise
    
    def test_query(self):        
        self.dataset_generator(['-w', "name = 'super cash back!'"])
    
    def test_query_no_data(self):
        _stderr = sys.stderr
        sys.stderr = sys.stdout
        def wrong_exc(exc=None):
            raise AssertionError("expected exit 2 %s" % (
                    exc and ("(raised: %s: %s)" % (exc.__class__, exc)) or ""))
        try:
            try:
                self.dataset_generator(['-w', "name = 'fooobzarius'"])
            except SystemExit as e:
                eq_(e.code, 2)
            except Exception as e:
                wrong_exc(e)
            else:
                wrong_exc()
        finally:
            sys.stderr = _stderr
            

class UsingTesttoolsTemplate(object):
    def __init__(self, *a,**kw):
        super(UsingTesttoolsTemplate, self).__init__(*a,**kw)
        self.args = [a for a in self.args] + ["--template=testtools"]
    
    def load_datasets(self, module, datasets):
        from testtools.fixtures import affix
        fxt = affix(*[d() for d in datasets])
        return fxt    
        
class UsingFixtureTemplate(object):
    def __init__(self, *a,**kw):
        super(UsingFixtureTemplate, self).__init__(*a,**kw)
        self.args = [a for a in self.args] + ["--template=fixture"]
    
    def visit_loader(self, loader):
        pass
    
    def load_datasets(self, module, datasets):
        fixture = self.create_fixture()
        self.visit_loader(fixture.loader)
        d = fixture.data(*datasets)
        d.setup()
        return d