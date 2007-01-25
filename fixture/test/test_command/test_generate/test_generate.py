
from nose.tools import eq_, raises
from fixture.command.generate import FixtureGenerator, UnrecognizedObject
    
class Stranger(object):
    """something that cannot produce data."""
    pass
        
@raises(UnrecognizedObject)
def test_unhandlable_object():
    generate = FixtureGenerator({})
    generate(".".join([Stranger.__module__, Stranger.__name__]))