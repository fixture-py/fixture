
import sys, inspect
from fixture.command.generate import (
        DataHandler, register_handler, FixtureSet, NoData, UnsupportedHandler)
from fixture import SQLAlchemyFixture
try:
    import sqlalchemy
except ImportError:
    sqlalchemy = False

class TableEnv(object):
    """a shared environment of sqlalchemy Table instances.
    
    can be initialized with python paths to objects or objects themselves
    """
    def __init__(self, *objects):
        self.objects = objects
        self.tablemap = {}
        for obj in self.objects:
            module = None
            if isinstance(obj, basestring):
                modpath = obj
                if modpath not in sys.modules:
                    # i.e. modpath from command-line option...
                    try:
                        if "." in modpath:
                            cut = modpath.rfind(".")
                            names = [modpath[cut+1:]]
                            parent = __import__(
                                    modpath[0:cut], globals(), locals(), names)
                            module = getattr(parent, names[0])
                        else:
                            module = __import__(modpath)
                    except:
                        etype, val, tb = sys.exc_info()
                        raise (
                            ImportError("%s: %s (while importing %s)" % (
                                etype, val, modpath)), None, tb)
                else:
                    module = sys.modules[modpath]
                    obj = module
            if module is None:
                module = inspect.getmodule(obj)
            self._find_objects(obj, module)
            
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
                        table, ", ".join([repr(p) for p in self.objects]))), tb
    
    def _find_objects(self, obj, module):
        from sqlalchemy.schema import Table
        from sqlalchemy.orm.mapper import (
                        has_mapper, class_mapper, object_mapper, 
                        mapper_registry)
        
        # get dict key/vals or dir() through object ...
        if not hasattr(obj, 'items'):
            def getitems():
                for name in dir(obj):
                    yield name, getattr(obj, name)
        else:
            getitems = obj.items
        for name, o in getitems():
            if isinstance(o, Table):
                self.tablemap.setdefault(o, {})
                self.tablemap[o]['name'] = name
                self.tablemap[o]['module'] = module
    
    def get_real_table(self, table):
        return getattr(self[table]['module'], self[table]['name'])

class SQLAlchemyHandler(DataHandler):
    """handles genration of fixture code from a sqlalchemy data source."""
    
    loadable_fxt_class = SQLAlchemyFixture
    
    class RecordSetAdapter(object):
        """adapts a sqlalchemy record set object for use in a 
        SQLAlchemyFixtureSet."""
        columns = None
        def __init__(self, obj):
            raise NotImplementedError("not a concrete implementation")
            
        def primary_key_from_instance(self, data):
            raise NotImplementedError
    
    def __init__(self, object_path, options, connection=None, **kw):
        from sqlalchemy import BoundMetaData, create_engine
        from sqlalchemy.ext.sessioncontext import SessionContext
        
        self.connection = connection
        super(SQLAlchemyHandler, self).__init__(object_path, options, **kw)
        if not self.connection:
            if self.options.dsn:
                self.meta = BoundMetaData(self.options.dsn)
            else:
                raise MisconfiguredHandler(
                        "--dsn option is required by %s" % self.__class__)
            self.connection = self.meta.engine.connect()
    
        self.session_context = SessionContext(
            lambda: sqlalchemy.create_session(bind_to=self.connection))
        
        self.env = TableEnv(*[self.obj.__module__] + self.options.env)
    
    def add_fixture_set(self, fset):
        t = self.env[fset.obj.table]
        self.template.add_import("from %s import %s" % (
                                        t['module'].__name__, t['name']))  
    
    def begin(self, *a,**kw):
        DataHandler.begin(self, *a,**kw)
        self.transaction = self.session_context.current.create_transaction()
        self.transaction.add(self.connection)
    
    def commit(self):
        self.transaction.commit()
    
    def rollback(self):
        self.transaction.rollback()
    
    def find(self, idval):
        self.rs = [self.obj.get(idval)]
        # session = self.session_context.current
        # self.rs = [session.query(self.obj).get(idval)]
        return self.rs
        
    def findall(self, query=None):
        """gets record set for query."""
        session = self.session_context.current
        if query:
            self.rs = session.query(self.obj).select_whereclause(query)
        else:
            self.rs = session.query(self.obj).select()
        if not len(self.rs):
            raise NoData("no data for query \"%s\" on %s" % (query, self.obj))
        return self.rs
    
    @staticmethod
    def recognizes(object_path, obj=None):
        """returns True if obj is not None.
        
        this method is just a starting point for sqlalchemy handlers.
        """
        if not sqlalchemy:
            raise UnsupportedHandler("sqlalchemy module not found")
        if obj is None:
            return False
        return True
    
    def sets(self):
        """yields FixtureSet for each row in SQLObject."""
        
        for row in self.rs:
            yield SQLAlchemyFixtureSet(row, self.obj, self.connection, self.env,
                                            adapter=self.RecordSetAdapter)

## NOTE: the order that handlers are registered in is important for discovering 
## sqlalchemy types...

class SQLAlchemyAssignedMapperHandler(SQLAlchemyHandler):    
    class RecordSetAdapter(SQLAlchemyHandler.RecordSetAdapter):
        def __init__(self, obj):
            self.mapped_class = obj
            
            if self.mapped_class.mapper.local_table:
                self.table = self.mapped_class.mapper.local_table
            elif self.mapped_class.mapper.select_table:
                self.table = self.mapped_class.mapper.select_table
            else:
                raise LookupError(
                    "not sure how to get a table from mapped class %s" % 
                                                        self.mapped_class)
            self.columns = self.mapped_class.mapper.columns
            self.id_attr = self.table.primary_key
            
        def primary_key_from_instance(self, data):
            return self.mapped_class.mapper.primary_key_from_instance(data)
            
    @staticmethod
    def recognizes(object_path, obj=None):
        if not SQLAlchemyHandler.recognizes(object_path, obj=obj):
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
        
        return False
        
register_handler(SQLAlchemyAssignedMapperHandler)

class SQLAlchemyTableHandler(SQLAlchemyHandler):        
    class RecordSetAdapter(SQLAlchemyHandler.RecordSetAdapter):
        def __init__(self, obj):
            self.table = obj
            self.columns = self.table.columns
            keys = [k for k in self.table.primary_key]
            if len(keys) != 1:
                raise ValueError("unsupported primary key type %s" % keys)
            self.id_attr = keys[0].key
        
        def primary_key_from_instance(self, data):
            key_str = []
            for k in self.table.primary_key:
                key_str.append(str(getattr(data, k.key)))
            return "_".join(key_str)
            
    @staticmethod
    def recognizes(object_path, obj=None):
        if not SQLAlchemyHandler.recognizes(object_path, obj=obj):
            return False
        
        from sqlalchemy.schema import Table
        if isinstance(obj, Table):
            raise NotImplementedError(
                    "Generating data with a table object is not implemented.  "
                    "Please use a mapped class or mapper object instead.  Or, "
                    "consider submitting a patch to support this.")
            return True
            
        return False
        
register_handler(SQLAlchemyTableHandler)

class SQLAlchemyMappedClassHandler(SQLAlchemyHandler):
    class RecordSetAdapter(SQLAlchemyHandler.RecordSetAdapter):
        def __init__(self, obj):
            self.columns = obj.c
            self.id_attr = obj.id.key
            
            from sqlalchemy.orm.mapper import object_mapper
            # is this safe?
            self.mapper = object_mapper(obj())
            
            if self.mapper.local_table:
                self.table = self.mapper.local_table
            elif self.mapper.select_table:
                self.table = self.mapper.select_table
            else:
                raise LookupError(
                    "not sure how to get a table from mapper %s" % 
                                                        self.mapper)
            
        def primary_key_from_instance(self, data):
            return self.mapper.primary_key_from_instance(data)
            
    @staticmethod
    def recognizes(object_path, obj=None):
        if not SQLAlchemyHandler.recognizes(object_path, obj=obj):
            return False
        if hasattr(obj, 'c'):
            if hasattr(obj.c, '__module__') and \
                    obj.c.__module__.startswith('sqlalchemy'):
                # eeesh
                return True
        
        return False
        
register_handler(SQLAlchemyMappedClassHandler)


class SQLAlchemyFixtureSet(FixtureSet):
    """a fixture set for a sqlalchemy record set."""
    
    def __init__(self, data, obj, connection, env, adapter=None):
        # print data, model
        FixtureSet.__init__(self, data)
        self.env = env
        self.connection = connection
        if adapter:
            self.obj = adapter(obj)
        else:
            self.obj = obj
        self.primary_key = None
        
        self.data_dict = {}
        for col in self.obj.columns:
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
            stmt = table.select(getattr(table.c, foreign_key.column.key)==value)
            rs = self.connection.execute(stmt)
            
            # adapter is always table adapter here, since that's
            # how we obtain foreign keys...
            subset = SQLAlchemyFixtureSet(
                        rs.fetchone(), table, self.connection, self.env,
                        adapter=SQLAlchemyTableHandler.RecordSetAdapter)
            return subset
            
        return value
    
    def get_id_attr(self):
        return self.obj.id_attr
    
    def obj_id(self):
        return self.env[self.obj.table]['name']
    
    def set_id(self):
        """returns id of this set (the primary key value)."""
        compid = self.obj.primary_key_from_instance(self.data)
        return "_".join([str(i) for i in compid])