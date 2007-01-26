
import sys
from fixture.command.generate import (
        DataHandler, register_handler, FixtureSet)
from fixture.loader import SqlAlchemyLoader
try:
    import sqlalchemy
except ImportError:
    sqlalchemy = False

class TableEnv(object):
    """a shared environment of sqlalchemy Table instances.
    """
    def __init__(self, *modpaths):
        self.modpaths = modpaths
        self.tablemap = {}
        for p in self.modpaths:
            if p not in sys.modules:
                # i.e. modpath from command-line option...
                try:
                    if "." in p:
                        cut = p.rfind(".")
                        names = [p[cut+1:]]
                        parent = __import__(
                                    p[0:cut], globals(), locals(), names)
                        module = getattr(parent, names[0])
                    else:
                        module = __import__(p)
                except:
                    etype, val, tb = sys.exc_info()
                    raise etype, ("%s (while importing %s)" % (val, p)), tb
            else:
                module = sys.modules[p]
            self._find_tables(module)
            
    def __contains__(self, key):
        return key in self.tablemap
    
    def __getitem__(self, key):
        try:
            return self.tablemap[key]
        except KeyError:
            etype, val, tb = sys.exc_info()
            raise etype, (
                "%s (looked in: %s)  You might need to add "
                "--env='path.to.module' ?" % (
                        val, ", ".join([p for p in self.modpaths])), tb)
    
    def _find_tables(self, module):
        from sqlalchemy.schema import Table
        for name in dir(module):
            o = getattr(module, name)
            if isinstance(o, Table):
                self.tablemap[o] = (name, module)
    
    def get_name(self, table):
        name, mod = self[table]
        return name
    
    def get_table(self, table):
        name, mod = self[table]
        return getattr(mod, name)

class SqlAlchemyHandler(DataHandler):
    """handles genration of fixture code from a sqlalchemy data source."""
    
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
        
        self.env = TableEnv(*[self.obj.__module__] + self.options.env)
    
    def add_fixture_set(self, fset):        
        name, mod = self.env[fset.model.mapper.mapped_table]
        self.template.add_import("from %s import %s" % (mod.__name__, name))  
    
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
            yield SqlAlchemyFixtureSet(row, self.obj, 
                                        self.session_context, self.env)
            
register_handler(SqlAlchemyHandler)


class SqlAlchemyFixtureSet(FixtureSet):
    """a fixture set for a sqlalchemy record set."""
    
    def __init__(self, data, model, session_context, env):
        FixtureSet.__init__(self, data)
        self.env = env
        self.session_context = session_context
        self.model = model
        self.primary_key = None
        
        self.data_dict = {}
        for col in self.model.mapper.columns:
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
            # this means that we are in a NULL column or foreign key
            # which could be perfectly legal.
            return None
            
        if foreign_key:
            from sqlalchemy import clear_mapper
            from sqlalchemy.ext.assignmapper import assign_mapper
            
            # probably a *much* better way to create dynamic mappers...
            class Object(object): 
                pass
                
            table = self.env.get_table(foreign_key.column.table)
            assign_mapper(  self.session_context, Object, table )
            rs = Object.get(value)
            
            # rs = self.meta.engine.execute(
            #                 foreign_key.column.table.select(
            #                     "%s = %%(%s)s" % (
            #                     foreign_key.column.name, 
            #                     foreign_key.column.name)), 
            #                         {foreign_key.column.name: value})
            subset = SqlAlchemyFixtureSet(
                        rs, Object, self.session_context, self.env)
            clear_mapper(Object.mapper)
            del Object
            return subset
            
        return value
    
    def get_id_attr(self):
        return self.model.id.key
    
    def obj_id(self):
        return self.env.get_name(self.model.mapper.mapped_table)
    
    def set_id(self):
        """returns id of this set (the primary key value)."""
        compid = self.model.mapper.primary_key_from_instance(self.data)
        return "_".join([str(i) for i in compid])