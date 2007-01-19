

class code_str(str):
    """string that reproduces without quotes.
    
    """
    def __repr__(self):
        return str.__repr__(self)[1:-1]
        
from generate import *

# load modules so they can register themselves (better way?)
try:
    import generate_sqlobject
except ImportError:
    pass
try:
    import generate_sqlalchemy
except ImportError:
    pass