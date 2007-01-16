
from nose.tools import eq_, raises
from fixture.generator import FixtureGenerator
    
class Stranger(object):
    """something that cannot produce data."""
    pass
        
@raises(ValueError)
def test_unhandlable_object():
    generate = FixtureGenerator({})
    generate(".".join([Stranger.__module__, Stranger.__name__]))
    