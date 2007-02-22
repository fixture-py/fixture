
"""each attribute indicates a supported module or feature."""
    
def supported(mod):
    try:
        __import__(mod)
    except ImportError:
        return False
    else:
        return True

sqlobject = supported('sqlobject')
sqlalchemy = supported('sqlalchemy')