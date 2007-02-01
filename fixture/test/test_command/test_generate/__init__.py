
import sys
import os
from nose.tools import eq_
from nose.exc import SkipTest
from fixture.test import conf
from fixture.command.generate import FixtureGenerator, run_generator

def setup():
    # every tests needs a real db conn :
    if not conf.POSTGRES_DSN:
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
    
    def assert_env_is_clean(self):
        raise NotImplementedError
    
    def assert_env_generated_ok(self, env):
        raise NotImplementedError
        
    def assert_data_loaded(self, data):
        raise NotImplementedError
    
    def load_env(self, module):
        raise NotImplementedError
    
    def run_generator(self, extra_args=[]):
        args = [a for a in self.args]
        if extra_args:
            args.extend(extra_args)
        
        self.assert_env_is_clean()
        code = run_generator(args)
        try:
            e = compile_(code)
            self.assert_env_generated_ok(e)
            data = self.load_env(e)
            self.assert_data_loaded(data)
        except:
            print code
            raise
    
    def test_query(self):
        self.run_generator(['-q', "name = 'super cash back!'"])
    
    def test_query_no_data(self):
        _stderr = sys.stderr
        sys.stderr = sys.stdout
        def wrong_exc(exc=None):
            raise AssertionError("expected exit 2 %s" % (
                    exc and ("(raised: %s: %s)" % (exc.__class__, exc)) or ""))
        try:
            try:
                self.run_generator(['-q', "name = 'fooobzarius'"])
            except SystemExit, e:
                eq_(e.code, 2)
            except Exception, e:
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
        self.visit_loader(module['fixture'].loader)
        d = module['fixture'].data(*datasets)
        d.setup()
        return d