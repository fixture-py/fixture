
"""each attribute indicates a supported module or feature."""

import os
import sys
    
def module_exists(mod):
    try:
        __import__(mod)
    except ImportError:
        return False
    else:
        return True

sqlobject = module_exists('sqlobject')
sqlalchemy = module_exists('sqlalchemy')
elixir = module_exists('elixir')
storm = module_exists('storm')
