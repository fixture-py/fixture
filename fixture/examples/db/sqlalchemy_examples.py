
"""examples for using sqlalchemy fixtures."""

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

from fixture.loader.sqlalchemy_loader import create_session_context

Category, Product, Offer = None, None, None

if sqlalchemy:
    from sqlalchemy import *
    from sqlalchemy.orm.mapper import global_extensions
    from sqlalchemy.ext.sessioncontext import SessionContext
    from sqlalchemy.ext.assignmapper import assign_mapper
    from fixture.loader import sqlalchemy_loader
    
    meta = DynamicMetaData()
    
    categories = Table("fixture_sqlalchemy_category", meta,
        Column("id", INT, primary_key=True),
        Column("name", String )
    )
    class Category(object):
        pass
    
    products = Table("fixture_sqlalchemy_product", meta,
        Column("id", INT, primary_key=True),
        Column("name", String ),
        Column("category_id", INT, ForeignKey("fixture_sqlalchemy_category.id")),
    )
    class Product(object):
        pass
    
    offers = Table("fixture_sqlalchemy_offer", meta,
        Column("id", INT, primary_key=True),
        Column("name", String ),
        Column("category_id", INT, ForeignKey("fixture_sqlalchemy_category.id")),
        Column("product_id", INT, ForeignKey("fixture_sqlalchemy_product.id")),
    )
    class Offer(object):
        pass

mappers_assigned = False

def setup_db(meta):
    assert sqlalchemy
    if not sqlalchemy_loader.session_context:
        create_session_context(meta)
    global mappers_assigned
    if not mappers_assigned:
        ctx = sqlalchemy_loader.session_context
        # this was the old way??
        # global_extensions.append(ctx.mapper_extension)
        
        assign_mapper(ctx, Category, categories)
        assign_mapper(ctx, Product, products)
        assign_mapper(ctx, Offer, offers)
        mappers_assigned = True
        
    # meta.connect(dsn)
    categories.create()
    products.create()
    offers.create()
    session = sqlalchemy_loader.session_context.current
    session.flush()
    session.clear()

def teardown_db(meta):
    assert sqlalchemy
    if not sqlalchemy_loader.session_context:
        create_session_context(meta)
    # meta.connect(dsn)
    categories.drop()
    products.drop()
    offers.drop()
    session = sqlalchemy_loader.session_context.current
    session.flush()
    session.clear()