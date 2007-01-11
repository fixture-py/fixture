
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
    
    # dbapi = conn.getConnection()
    # c = dbapi.cursor()
    # for tb in (Offer, Product, Category):
    #     c.execute("delete from %s" % tb.sqlmeta.table)
    #     dbapi.commit()
    
    ## apparently, sqlobject is retarded and sometimes 
    ## this can cause an infinite loop that can't be interrupted.  excellent!
    for tb in (Offer, Product, Category):
        tb.dropTable(connection=conn)
