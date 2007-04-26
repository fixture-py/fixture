
import sys
from nose.tools import eq_, raises, with_setup
from fixture.test import attr
from fixture.command.generate import *
    
class Stranger(object):
    """something that cannot produce data."""
    pass

@raises(UnrecognizedObject)
@attr(unit=True)
def test_unhandlable_object():
    generate = DataSetGenerator({})
    generate(".".join([Stranger.__module__, Stranger.__name__]))

class MyHandler(DataHandler):
    @staticmethod
    def recognizes(obj_path, obj=None):
        if obj_path == "myhandler.object_path":
            return True
                
def register_myhandler():
    register_handler(MyHandler)

_saved_registry = [h for h in handler_registry]
def reset_handlers():
    handler_registry[:] = [h for h in _saved_registry]

@attr(unit=True)
@with_setup(setup=register_myhandler, teardown=reset_handlers)
def test_dataset_handler():    
    g = DataSetGenerator({})
    hnd = g.get_handler("myhandler.object_path")
    assert isinstance(hnd, MyHandler)
    
    
@attr(unit=True)
@raises(UnrecognizedObject)
@with_setup(setup=register_myhandler, teardown=reset_handlers)
def test_unrecognized_dataset_handler():
    g = DataSetGenerator({})
    hnd = g.get_handler("NOTHONG")
    
@attr(unit=True)
def test_requires_option():
    required_idents = []
    def mock_require(ident):
        required_idents.append(ident)
    import pkg_resources
    orig_require = pkg_resources.require
    pkg_resources.require = mock_require
    sys.stderr = sys.stdout
    try:
        try:
            dataset_generator([ 'bad.object.path', 
                '--require-egg=foo==1.0', '--require-egg=baz>=2.0b'])
        except SystemExit, e:
            pass
    finally:
        pkg_resources.require = orig_require    
        sys.stderr = sys.__stderr__
    eq_(required_idents, ['foo==1.0', 'baz>=2.0b'])