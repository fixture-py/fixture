
class code_str(str):
    """string that reproduces without quotes.
    
    """
    def __repr__(self):
        return str.__repr__(self)[1:-1]

from fixture.command.generate import generate
__doc__ = generate.__doc__
from fixture.command.generate.generate import *

# load modules so they can register themselves (better way?)
try:
    from fixture.command.generate import generate_sqlobject
except ImportError:
    pass
try:
    from fixture.command.generate import generate_sqlalchemy
except ImportError:
    pass