
"""examples for using SQLObject fixtures."""

try:
    import sqlobject
except ImportError:
    sqlobject = None

F_Category, F_Product, F_Offer = None, None, None

if sqlobject:
    from sqlobject import *
    
    class F_Category(SQLObject):
        name = StringCol()

    class F_Product(SQLObject):
        name = StringCol()
        category = ForeignKey('F_Category')

    class F_Offer(SQLObject):
        name = StringCol()
        category = ForeignKey('F_Category')
        product = ForeignKey('F_Product')

def setup_db(conn):
    F_Category.createTable(connection=conn)
    F_Product.createTable(connection=conn)
    F_Offer.createTable(connection=conn)

def teardown_db(conn):
    F_Category.dropTable(connection=conn, cascade=True)
    F_Product.dropTable(connection=conn, cascade=True)
    F_Offer.dropTable(connection=conn, cascade=True)
