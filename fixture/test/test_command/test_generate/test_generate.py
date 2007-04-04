
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

@attr(unit=True)
@with_setup(setup=register_myhandler, teardown=clear_handlers)
def test_dataset_handler():    
    g = DataSetGenerator({})
    hnd = g.get_handler("myhandler.object_path")
    assert isinstance(hnd, MyHandler)
    
    
@attr(unit=True)
@raises(UnrecognizedObject)
@with_setup(setup=register_myhandler, teardown=clear_handlers)
def test_unrecognized_dataset_handler():
    g = DataSetGenerator({})
    hnd = g.get_handler("NOTHONG")
    
    
    