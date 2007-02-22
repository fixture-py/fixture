
"""each attribute indicates a supported module or feature."""

# hopefully there's a better way to do this....
# from fixture import TempIO
# t = TempIO()
# mod = compile("""
# from __future__ import with_statement
# """, 
#                 t.join("bootstrap_with.py"), 'exec')
# try:
#     eval(mod)
# except SyntaxError:
#     with_statement = False
# else:
#     with_statement = True
    
def supported(mod):
    try:
        __import__(mod)
    except ImportError:
        return False
    else:
        return True

sqlobject = supported('sqlobject')
sqlalchemy = supported('sqlalchemy')