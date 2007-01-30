
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
            self._find_objects(module)
            
    def __contains__(self, key):
        return key in self.tablemap
    
    def __getitem__(self, table):
        try:
            return self.tablemap[table]
        except KeyError:
            etype, val, tb = sys.exc_info()
            raise LookupError, (
                "Could not locate original declaration of Table %s "
                "(looked in: %s)  You might need to add "
                "--env='path.to.module'?" % (
                        table, ", ".join([p for p in self.modpaths]))), tb
    
    def _find_objects(self, module):
        from sqlalchemy.schema import Table
        from sqlalchemy.orm.mapper import (
                        has_mapper, class_mapper, object_mapper, 
                        mapper_registry)
        for name in dir(module):
            o = getattr(module, name)
            if isinstance(o, Table):
                self.tablemap.setdefault(o, {})
                self.tablemap[o]['name'] = name
                self.tablemap[o]['module'] = module
                # for k in mapper_registry:
                #     print k, mapper_registry[k]
                # self.tablemap[o]['mapped_class'] = object_mapper(o)
                
                ## whoa?? how else can I find an existing mapper for a table?
                
            # if has_mapper(o):
            #     mapper = class_mapper(o, entity_name=o._entity_name)
            #     if not hasattr(mapper, local_table):
            #         raise NotImplementedError(
            #             "not sure how to handle a mapper like %s that does not "
            #             "contain a local_table" % mapper)
            #     t = mapper.local_table
            #     self.tablemap.setdefault(t, {})
            #     self.tablemap[t]['mapped_class'] = o
    
    # def get_mapped_class(self, table):
    #     try:
    #         return self[table]['mapped_class']
    #     except KeyError:
    #         # fixme: repr the env here...
    #         raise LookupError(
    #             "no mapped class found for table %s in env" % (table))
    
    def get_name(self, table):
        return self[table]['name']
    
    def get_table(self, table):
        return getattr(self[table]['module'], self[table]['name'])

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
        """returns True if obj is a mapped sqlalchemy object
        """
        if not sqlalchemy:
            raise UnsupportedHandler("sqlalchemy module not found")
        if obj is None:
            return False
        
        def isa_mapper(mapper):
            from sqlalchemy.orm.mapper import Mapper
            if type(mapper)==Mapper:
                return True
                
        if hasattr(obj, 'mapper'):
            # i.e. assign_mapper ...
            if isa_mapper(obj.mapper):
                return True
        if hasattr(obj, '_mapper'):
            # i.e. sqlsoup ??
            if isa_mapper(obj._mapper):
                return True
            
        from sqlalchemy.orm.mapper import has_mapper
        if has_mapper(obj):
            # i.e. has been used in a session (is this likely?)
            return True
        
        from sqlalchemy.schema import Table
        if isinstance(obj, Table):
            raise NotImplementedError(
                "using a table object, like %s, is not implemented.  perhaps "
                "it should be.  for now you will have to pass in a mapper "
                "instead" % obj)
        
        return False
    
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
            from sqlalchemy.ext.assignmapper import assign_mapper
            from sqlalchemy.ext.sqlsoup import class_for_table
                
            table = foreign_key.column.table
            try:
                MappedClass = self.env.get_mapped_class(table)
            except LookupError:
                # do we need to connect the session here??
                MappedClass = class_for_table(table)
            
            rs = MappedClass.get(value)
            
            # rs = self.meta.engine.execute(
            #                 foreign_key.column.table.select(
            #                     "%s = %%(%s)s" % (
            #                     foreign_key.column.name, 
            #                     foreign_key.column.name)), 
            #                         {foreign_key.column.name: value})
            subset = SqlAlchemyFixtureSet(
                        rs, MappedClass, self.session_context, self.env)
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