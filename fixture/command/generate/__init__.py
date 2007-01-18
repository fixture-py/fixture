

class code_str(str):
    """string that reproduces without quotes.
    
    """
    def __repr__(self):
        return str.__repr__(self)[1:-1]
        
from generator import *

# load modules so they can register themselves (better way?)
try:
    import sqlobject_generator
except ImportError:
    pass