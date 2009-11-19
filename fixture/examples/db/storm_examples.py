
"""examples for using Storm fixtures."""

try:
    import storm
except ImportError:
    storm = None

Category, Product, Offer = None, None, None

if storm:
    from storm.locals import *
    
    class Category(Storm):
        __storm_table__ = 'fixture_storm_category'
        id = Int(primary=True)
        name = RawStr()

    class Product(Storm):
        __storm_table__ = 'fixture_storm_product'
        id = Int(primary=True)
        name = RawStr()
        category_id = Int()
        category = Reference(category_id, Category.id)

    class Offer(Storm):
        __storm_table__ = 'fixture_storm_offer'
        id = Int(primary=True)
        name = RawStr()
        category_id = Int()
        category = Reference(category_id, Category.id)
        product_id = Int()
        product = Reference(product_id, Product.id)

def setup_db(conn):
    assert conn is not None
    conn.rollback()
    # NOTE: this SQL works in postgres and sqlite:
    conn.execute(SQL("""CREATE TABLE fixture_storm_category (
      id serial primary key,
      name varchar(60)
      )"""))
    assert conn.find(Category).count() == 0
    conn.execute(SQL("""CREATE TABLE fixture_storm_product (
       id serial primary key,
       name varchar(60),
       category_id integer
      )"""))
    assert conn.find(Product).count() == 0
    conn.execute(SQL("""CREATE TABLE fixture_storm_offer (
       id serial primary key,
       name varchar(60),
       category_id integer,
       product_id integer
      )"""))
    assert conn.find(Offer).count() == 0
    conn.commit()

def teardown_db(conn):
    assert conn is not None
    
    conn.rollback()
    for tb in (Offer, Product, Category):
        conn.execute(SQL('drop table '+tb.__storm_table__))
    conn.commit()
