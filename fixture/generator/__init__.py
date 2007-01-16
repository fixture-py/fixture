
from generator import *

# load modules so they can register themselves (better way?)
try:
    import sqlobject_handler
except ImportError:
    pass