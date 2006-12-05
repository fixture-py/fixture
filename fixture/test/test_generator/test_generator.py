
from nose.tools import eq_, raises
from fixture.generator import FixtureGenerator
    
@raises(ValueError)
def test_unhandlable_object():
    generate = FixtureGenerator()
    
    class Stranger(object):
        """something that cannot produce data."""
        pass
        
    generate(Stranger())
    