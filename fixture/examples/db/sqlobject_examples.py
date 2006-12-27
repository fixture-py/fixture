
"""examples for using SQLObject fixtures."""

try:
    import sqlobject
except ImportError:
    sqlobject = None

Category, Product, Offer = None, None, None

if sqlobject:
    from sqlobject import *
    
    class Category(SQLObject):
        class sqlmeta:
            table = 'fixture_sqlobject_category'
        name = StringCol()

    class Product(SQLObject):
        class sqlmeta:
            table = 'fixture_sqlobject_product'
        name = StringCol()
        category = ForeignKey('Category')

    class Offer(SQLObject):
        class sqlmeta:
            table = 'fixture_sqlobject_offer'
        name = StringCol()
        category = ForeignKey('Category')
        product = ForeignKey('Product')

def setup_db(conn):
    assert conn is not None
    Category.createTable(connection=conn)
    Product.createTable(connection=conn)
    Offer.createTable(connection=conn)

def teardown_db(conn):
    assert conn is not None
    Category.dropTable(connection=conn, cascade=True)
    Product.dropTable(connection=conn, cascade=True)
    Offer.dropTable(connection=conn, cascade=True)
