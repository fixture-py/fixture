
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
        except SystemExit:
            pass
    finally:
        pkg_resources.require = orig_require    
        sys.stderr = sys.__stderr__
    eq_(required_idents, ['foo==1.0', 'baz>=2.0b'])

def some_function():
    pass

class SomeClass(object):
    def some_method(self):
        pass

@attr(unit=1)
def test_resolve_path_to_function():
    eq_(resolve_function_path("%s:some_function" % __name__), some_function)
    
@attr(unit=1)
def test_resolve_path_to_method():
    eq_(resolve_function_path("%s:SomeClass.some_method" % __name__), SomeClass.some_method)
    
@attr(unit=1)
def test_resolve_path_to_module():
    # Note that this is not realistic.  I think we'd always want a callable
    eq_(resolve_function_path("%s" % __name__), sys.modules[__name__])

@attr(unit=1)
@raises(ImportError)
def test_resolve_bad_path():
    resolve_function_path("nomoduleshouldbenamedthis.nowhere:Babu")
    