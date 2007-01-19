
"""examples for using sqlalchemy fixtures."""

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

Category, Product, Offer = None, None, None

if sqlalchemy:
    from sqlalchemy import *
    from sqlalchemy.orm.mapper import global_extensions
    from sqlalchemy.ext.sessioncontext import SessionContext
    from sqlalchemy.ext.assignmapper import assign_mapper
    
    categories = Table("fixture_sqlalchemy_category",
        Column("id", INT, primary_key=True),
        Column("name", String )
    )
    class Category(object):
        pass
    
    products = Table("fixture_sqlalchemy_product",
        Column("id", INT, primary_key=True),
        Column("name", String ),
        Column("category_id", INT, 
                ForeignKey("fixture_sqlalchemy_category.id")),
    )
    class Product(object):
        pass
    
    offers = Table("fixture_sqlalchemy_offer",
        Column("id", INT, primary_key=True),
        Column("name", String ),
        Column("category_id", INT, 
                ForeignKey("fixture_sqlalchemy_category.id")),
        Column("product_id", INT, ForeignKey("fixture_sqlalchemy_product.id")),
    )
    class Offer(object):
        pass

def setup_db(meta, session_context, **kw):
    assert sqlalchemy
    
    def assign_and_create(obj, table, **localkw):
        table.tometadata(meta)
        sendkw = dict([(k,v) for k,v in localkw.items()])
        sendkw.update(kw)
        assign_mapper(session_context, obj, table, **sendkw)
        table.create(meta.engine)
    
    session = session_context.current
    
    assign_and_create(Category, categories)
    assign_and_create(Product, products)
    assign_and_create(Offer, offers)
    
    session.flush()
    session.clear()

def teardown_db(meta, session_context):
    assert sqlalchemy
    meta.drop_all()
    
    session = session_context.current
    session.flush()
    
    sqlalchemy.orm.clear_mappers()
    
    