
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

class b:
    def __enter__(): pass
    def __exit__(): pass
c = """
with b():
    with_statement = True
"""
try:
    eval(c)
except SyntaxError:
    with_statement = None