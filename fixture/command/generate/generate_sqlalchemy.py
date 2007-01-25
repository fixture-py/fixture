
from fixture.command.generate import (
        DataHandler, register_handler, FixtureSet)
from fixture.loader import SqlAlchemyLoader
try:
    import sqlalchemy
except ImportError:
    sqlalchemy = False

class SqlAlchemyHandler(DataHandler):
    
    loader_class = SqlAlchemyLoader
    
    def __init__(self, *a,**kw):
        DataHandler.__init__(self, *a,**kw)
        if self.options.dsn:
            from sqlalchemy import BoundMetaData
            from sqlalchemy.ext.sessioncontext import SessionContext
            self.meta = BoundMetaData(self.options.dsn)
            self.session_context = SessionContext(
                lambda: sqlalchemy.create_session(bind_to=self.meta.engine))
        else:
            raise MisconfiguredHandler(
                    "--dsn option is required by %s" % self.__class__)
    
    def add_fixture_set(self, fset):
        # from sqlobject.classregistry import findClass
        # so_class = fset.obj_id()
        # kls = findClass(so_class)
        # # this maybe isn't very flexible ...
        
        kls = fset.model
        self.template.add_import("from %s import %s" % (
                            kls.__module__, kls.__name__))  
        ### next, need to assign_mapper
    
    def find(self, idval):
        raise NotImplementedError
        # self.rs = [self.obj.get(idval)]
        
    def findall(self, query):
        """gets record set for query."""
        session = self.session_context.current
        self.rs = session.query(self.obj).select_whereclause(query)
    
    @staticmethod
    def recognizes(object_path, obj=None):
        """returns True if obj is a SQLObject class.
        """
        if not sqlalchemy:
            raise UnsupportedHandler("sqlalchemy module not found")
        if obj is None:
            return False
            
        # support something other than mapped objects??
        if not hasattr(obj, 'mapper'):
            return False
        from sqlalchemy.orm.mapper import Mapper
        if not type(obj.mapper)==Mapper:
            return False
        
        return True
    
    def sets(self):
        """yields FixtureSet for each row in SQLObject."""
        
        for row in self.rs:
            yield SqlAlchemyFixtureSet(row, self.obj, self.session_context)
            
register_handler(SqlAlchemyHandler)


class SqlAlchemyFixtureSet(FixtureSet):
    """a fixture set for a sqlalchemy row object."""
    
    def __init__(self, data, model, session_context):
        FixtureSet.__init__(self, data)
        # self.meta = meta
        self.session_context = session_context
        self.model = model
        self.foreign_key_class = {}
        self.primary_key = None
        
        self.data_dict = {}
        for col in self.model.mapper.columns:
            if not hasattr(self.data, col.name):
                # this is sort of strange:
                # we seem to get back referenced foreign key columns.  i.e. a 
                # category mapper's columns might have category_id if an offer 
                # table had declared its category_id as a foreign key to 
                # category.  the link is actually to category.id and we've 
                # already resolved it all, so continue??
                continue
            sendkw = {}
            if col.foreign_key:
                sendkw['foreign_key'] = col.foreign_key
                
            val = self.get_col_value(col.name, **sendkw)
            self.data_dict[col.name] = val
    
    def attr_to_db_col(self, col):
        return col.name
    
    def get_col_value(self, colname, foreign_key=None):
        """transform column name into a value or a
        new set if it's a foreign key (recursion).
        """
        value = getattr(self.data, colname)
        if value is None:
            # this means that we are in a NULL foreign key
            # which could be perfectly legal.
            return None
            
        ## raise an error when there are multiple foreign keys?
        if foreign_key:
            # print foreign_key.column.table
            # print dir(foreign_key)
            from sqlalchemy import clear_mapper
            from sqlalchemy.ext.assignmapper import assign_mapper
            
            # probably a *much* better way to create dynamic mappers...
            class Object(object): 
                pass
            Object.__name__ = "%s_" % foreign_key.column.table
            
            assign_mapper(  self.session_context, Object, 
                            foreign_key.column.table )
            rs = Object.get(value)
            
            # rs = self.meta.engine.execute(
            #                 foreign_key.column.table.select(
            #                     "%s = %%(%s)s" % (
            #                     foreign_key.column.name, 
            #                     foreign_key.column.name)), 
            #                         {foreign_key.column.name: value})
            subset = SqlAlchemyFixtureSet(
                    rs, Object, self.session_context)
            clear_mapper(Object.mapper)
            del Object
            return subset
            
            
        if colname in self.foreign_key_class:
            raise NotImplementedError
        else:
            return value
        #     model = findClass(self.foreign_key_class[colname])
        #     rs = model.get(value, connection=self.connection)
        #     return SQLObjectFixtureSet(rs, model, connection=self.connection)
        # else:
        #     return value
    
    def get_id_attr(self):
        return self.model.id.key
    
    def set_id(self):
        """returns id of this set (the primary key value)."""
        compid = self.model.mapper.primary_key_from_instance(self.data)
        return "_".join([str(i) for i in compid])