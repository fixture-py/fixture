
from nose.tools import eq_
from fixture.test import attr
from fixture.base import Fixture

mock_call_log = []

def reset_mock_call_log():
    mock_call_log[:] = []
    
class MockLoader(object):
    def load(self, data):
        mock_call_log.append((self.__class__, 'load', data.__class__))
    def unload(self):
        mock_call_log.append((self.__class__, 'unload'))

class StubSuperSet(object):
    def __init__(self, *a,**kw):
        pass

class StubDataset:
    @classmethod
    def shared_instance(self, *a, **kw):
        return self()
class StubDataset1(StubDataset):
    pass
class StubDataset2(StubDataset):
    pass
    
class TestFixture:
    def setUp(self):
        reset_mock_call_log()
        self.fxt = Fixture(loader=MockLoader(), dataclass=StubSuperSet)
    
    def tearDown(self):
        reset_mock_call_log()
    
    @attr(unit=1)
    def test_data_sets_up_and_tears_down_data(self):
        data = self.fxt.data(StubDataset1, StubDataset2)
        data.setup()
        eq_(mock_call_log[-1], (MockLoader, 'load', StubSuperSet))
        data.teardown()
        eq_(mock_call_log[-1], (MockLoader, 'unload'))
        
    @attr(unit=1)
    def test_data_implements_with_interface(self):
        data = self.fxt.data(StubDataset1, StubDataset2)
        data = data.__enter__()
        eq_(mock_call_log[-1], (MockLoader, 'load', StubSuperSet))
        data.__exit__(None, None, None)
        eq_(mock_call_log[-1], (MockLoader, 'unload'))
    
    @attr(unit=1)
    def test_with_data_decorates_a_callable(self):
        @self.fxt.with_data(StubDataset1, StubDataset2)
        def some_callable(data):
            mock_call_log.append(('some_callable', data.__class__))
        some_callable()
        eq_(mock_call_log[-3], (MockLoader, 'load', StubSuperSet))
        eq_(mock_call_log[-2], ('some_callable', Fixture.Data))
        eq_(mock_call_log[-1], (MockLoader, 'unload'))
        