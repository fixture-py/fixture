import sys

import nose.case
import nose.loader
import nose.tools
from fixture.base import Fixture
from fixture.test import attr, SilentTestRunner
from nose.tools import eq_, raises
from six import StringIO


mock_call_log = []

def reset_mock_call_log():
    mock_call_log[:] = []
    
class MockLoader(object):
    def load(self, data):
        mock_call_log.append((self.__class__, 'load', data.__class__))
    def unload(self):
        mock_call_log.append((self.__class__, 'unload'))
        
class AbusiveMockLoader(object):
    def load(self, data):
        mock_call_log.append((self.__class__, 'load', data.__class__))
    def unload(self):
        raise ValueError("An exception during teardown")

class StubSuperSet(object):
    def __init__(self, *a,**kw):
        pass

class StubDataset:
    @classmethod
    def shared_instance(self, *a, **kw):
        return self()
class StubDataset1(StubDataset): pass
class StubDataset2(StubDataset): pass
    
class TestFixture:
    def setUp(self):
        reset_mock_call_log()
        self.fxt = Fixture(loader=MockLoader(), dataclass=StubSuperSet)
    
    def tearDown(self):
        reset_mock_call_log()
    
    @attr(unit=True)
    def test_data_sets_up_and_tears_down_data(self):
        data = self.fxt.data(StubDataset1, StubDataset2)
        data.setup()
        eq_(mock_call_log[-1], (MockLoader, 'load', StubSuperSet))
        data.teardown()
        eq_(mock_call_log[-1], (MockLoader, 'unload'))
        
    @attr(unit=True)
    def test_data_implements_with_statement(self):
        data = self.fxt.data(StubDataset1, StubDataset2)
        data = data.__enter__()
        eq_(mock_call_log[-1], (MockLoader, 'load', StubSuperSet))
        data.__exit__(None, None, None)
        eq_(mock_call_log[-1], (MockLoader, 'unload'))
    
    @attr(unit=True)
    def test_with_data_decorates_a_callable(self):
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            mock_call_log.append(('some_callable', data.__class__))
        some_callable()
        eq_(mock_call_log[0], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[1], ('some_callable', Fixture.Data))
        eq_(mock_call_log[2], (MockLoader, 'unload'))
        
    @attr(unit=True)
    def test_with_data_calls_teardown_on_error(self):
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            raise RuntimeError("a very bad thing")
        raises(RuntimeError)(some_callable)()
        eq_(mock_call_log[0], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[1], (MockLoader, 'unload'))
        
    @attr(unit=True)
    def test_with_data_aborts_teardown_on_interrupt(self):
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            raise KeyboardInterrupt
        raises(KeyboardInterrupt)(some_callable)()
        eq_(mock_call_log[0], (MockLoader, 'load', StubSuperSet))
        eq_(len(mock_call_log), 1, 
            "unexpected additional calls were made: %s" % mock_call_log)
            
    @attr(unit=True)
    def test_with_data_raises_exception_in_teardown(self):
        self.fxt.loader = AbusiveMockLoader()
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            pass
        raises(ValueError)(some_callable)()
        eq_(mock_call_log[0], (AbusiveMockLoader, 'load', StubSuperSet))
        
    @attr(unit=True)
    def test_with_data_does_soft_teardown_on_exception(self):
        self.fxt.loader = AbusiveMockLoader()
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            raise RuntimeError("a very bad thing")
        err = StringIO()
        sys.stderr = err
        try:
            raises(RuntimeError)(some_callable)()
        finally:
            sys.stderr = sys.__stderr__
        saved_err = err.getvalue()
        assert "ValueError: An exception during teardown" in \
            saved_err, (
                "unexpected stderr capture: \n<<<<<<\n%s>>>>>>\n" % saved_err)
        eq_(mock_call_log[0], (AbusiveMockLoader, 'load', StubSuperSet))
        
    @attr(unit=True)
    def test_with_data_decorates_a_generator(self):
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_generator():
            def generated_test(data, step):
                mock_call_log.append(('some_generator', data.__class__, step))
            for step in range(4):
                yield generated_test, step
        
        loader = nose.loader.TestLoader()
        # 0.10 only ....
        suite = loader.loadTestsFromGenerator(some_generator, None)
        SilentTestRunner().run(suite)
        
        eq_(mock_call_log[0], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[1], ('some_generator', Fixture.Data, 0))
        eq_(mock_call_log[2], (MockLoader, 'unload'))
        eq_(mock_call_log[3], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[4], ('some_generator', Fixture.Data, 1))
        eq_(mock_call_log[5], (MockLoader, 'unload'))
        eq_(mock_call_log[6], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[7], ('some_generator', Fixture.Data, 2))
        eq_(mock_call_log[8], (MockLoader, 'unload'))
        eq_(mock_call_log[9], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[10], ('some_generator', Fixture.Data, 3))
        
    @attr(unit=True)
    def test_generated_tests_call_teardown_on_error(self):
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_generator():
            @raises(RuntimeError)
            def generated_test(data, step):
                mock_call_log.append(('some_generator', data.__class__, step))
                raise RuntimeError
            for step in range(2):
                yield generated_test, step
                
        loader = nose.loader.TestLoader()
        # 0.10 only ....
        suite = loader.loadTestsFromGenerator(some_generator, None)
        SilentTestRunner().run(suite)
            
        eq_(mock_call_log[0], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[1], ('some_generator', Fixture.Data, 0))
        eq_(mock_call_log[2], (MockLoader, 'unload'))
        eq_(mock_call_log[3], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[4], ('some_generator', Fixture.Data, 1))
        eq_(mock_call_log[5], (MockLoader, 'unload'))
        
    @attr(unit=True)
    def test_generated_raises_exception_in_teardown(self):
        self.fxt.loader = AbusiveMockLoader()
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_generator():
            def generated_test(data, step):
                mock_call_log.append(('some_generator', data.__class__, step))
            for step in range(2):
                yield generated_test, step
                
        loader = nose.loader.TestLoader()
        # 0.10 only ....
        suite = loader.loadTestsFromGenerator(some_generator, None)
        @raises(Exception)
        def run_tests():
            SilentTestRunner().run(suite)
        run_tests()
            
        eq_(mock_call_log[0], (AbusiveMockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[1], ('some_generator', Fixture.Data, 0))
        
    @attr(unit=True)
    def test_generated_error_raises_soft_exception_in_teardown(self):
        self.fxt.loader = AbusiveMockLoader()
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_generator():
            def generated_test(data, step):
                mock_call_log.append(('some_generator', data.__class__, step))
                raise RuntimeError("error raised from some_generator")
            for step in range(2):
                yield generated_test, step
                
        loader = nose.loader.TestLoader()
        loader = nose.loader.TestLoader()
        # 0.10 only ....
        suite = loader.loadTestsFromGenerator(some_generator, None)

        @raises(RuntimeError)
        def run_tests():
            SilentTestRunner().run(suite)
                
        err = StringIO()
        sys.stderr = err
        try:
            try:
                run_tests()
            except Exception:
                etype, val, tb = sys.exc_info()
                assert 'error raised from some_generator' in str(val), (
                    "Unexpected: %s" % val)
            else:
                assert False, "expected an exception to be raised"
        finally:
            sys.stderr = sys.__stderr__
        saved_err = err.getvalue()
        assert "ValueError: An exception during teardown" in \
            saved_err, (
                "unexpected stderr capture: \n<<<<<<\n%s>>>>>>\n" % saved_err)
            
        eq_(mock_call_log[0], (AbusiveMockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[1], ('some_generator', Fixture.Data, 0))
        
    @attr(unit=True)
    def test_with_data_preserves_a_decorated_callable(self):
        def my_custom_setup():
            mock_call_log.append('my_custom_setup')
        def my_custom_teardown():
            mock_call_log.append('my_custom_teardown')
        @nose.tools.with_setup(
            setup=my_custom_setup, teardown=my_custom_teardown)
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            mock_call_log.append(('some_callable', data.__class__))
        case = nose.case.FunctionTestCase(some_callable)
        SilentTestRunner().run(case)
        eq_(mock_call_log[-5], 'my_custom_setup')
        eq_(mock_call_log[-4], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[-3], ('some_callable', Fixture.Data))
        eq_(mock_call_log[-2], (MockLoader, 'unload'))
        eq_(mock_call_log[-1], 'my_custom_teardown')
        