
"""each attribute indicates a supported module or feature."""

try:
    import sqlobject
except ImportError:
    sqlobject = None

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