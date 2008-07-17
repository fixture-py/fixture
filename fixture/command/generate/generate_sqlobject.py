
"""support to generate SQLObject-based fixtures."""

from fixture.style import camel_to_under
from fixture import SQLObjectFixture
from fixture.command.generate import (
    DataHandler, FixtureSet, register_handler, code_str, 
    UnsupportedHandler, MisconfiguredHandler, NoData )
            
try:
    import sqlobject
except ImportError:
    sqlobject = None

class SQLObjectHandler(DataHandler):
    
    loadable_fxt_class = SQLObjectFixture
    
    def __init__(self, *a,**kw):
        DataHandler.__init__(self, *a,**kw)
        from sqlobject import sqlhub, connectionForURI
        if self.options.dsn:
            self.connection = connectionForURI(self.options.dsn)
        else:
            raise MisconfiguredHandler(
                    "--dsn option is required by %s" % self.__class__)
        if len(self.options.env):
            raise NotImplementedError(
                "sqlobject is not using --env; perhaps we just need to import "
                "the envs so that findClass knows about its objects?")
    
    def add_fixture_set(self, fset):
        from sqlobject.classregistry import findClass
        so_class = fset.obj_id()
        kls = findClass(so_class)
        # this maybe isn't very flexible ...
        self.template.add_import("from %s import %s" % (
                            kls.__module__, so_class))  
    
    def find(self, idval):
        self.rs = [self.obj.get(idval)]
        
    def findall(self, query):
        """gets record set for query."""        
        self.rs = self.obj.select(query, connection=self.connection)
        if not self.rs.count():
            raise NoData("no data for query \"%s\" on object %s" % (
                                                        query, self.obj))
    
    def fxt_type(self):
        return 'SOFixture'
    
    @staticmethod
    def recognizes(object_path, obj=None):
        """returns True if obj is a SQLObject class.
        """
        if not sqlobject:
            raise UnsupportedHandler("sqlobject module not found")
        if obj is None:
            return False
        from sqlobject.declarative import DeclarativeMeta
        if type(obj) is DeclarativeMeta and obj.__name__ not in (
                        'SQLObject', 'sqlmeta', 'ManyToMany', 'OneToMany'):
            return True      
    
    def sets(self):
        """yields FixtureSet for each row in SQLObject."""
        for row in self.rs:
            yield SQLObjectFixtureSet(row, self.obj, connection=self.connection)
            
register_handler(SQLObjectHandler)

class SQLObjectFixtureSet(FixtureSet):
    """a fixture set for a SQLObject row."""
    
    def __init__(self, data, model, connection=None):
        FixtureSet.__init__(self, data)
        self.connection = connection
        self.model = model
        self.meta = model.sqlmeta
        self.foreign_key_class = {}
        self.primary_key = None
        
        self.understand_columns()
        
        # NOTE: primary keys are not included in columnList
        # so we need to find it ...
        
        cols = [self.meta.style.idForTable(self.meta.table)]
        cols.extend([self.attr_to_db_col(c) for c in self.meta.columnList])
    
        # even though self.meta.idName tells us the real col name, when 
        # accessing object properties sqlobject wants you to say object.id,
        # for which it proxies the real id column name
        vals = [getattr(self.data, 'id')]
        vals.extend([self.get_col_value(c.name) for c in self.meta.columnList])
    
        self.data_dict = dict(zip(cols, vals))
    
    def attr_to_db_col(self, col):
        if col.dbName is not None:
            return col.dbName
        else:
            return self.meta.style.pythonAttrToDBColumn(col.name)
    
    def get_col_value(self, colname):
        """transform column name into a value or a
        new set if it's a foreign key (recursion).
        """
        from sqlobject.classregistry import findClass
        value = getattr(self.data, colname)
        if value is None:
            # this means that we are in a NULL foreign key
            # which could be perfectly legal.
            return None
            
        if self.foreign_key_class.has_key(colname):
            model = findClass(self.foreign_key_class[colname])
            rs = model.get(value, connection=self.connection)
            return SQLObjectFixtureSet(rs, model, connection=self.connection)
        else:
            return value
    
    def get_id_attr(self):
        meta = self.meta
        id_attr = meta.style.idForTable(meta.table)
        return id_attr
    
    def mk_var_name(self):
        """returns a variable name for the instance of the fixture class.
        """
        fxt_cls_name = self.obj_id()
        return "_".join([camel_to_under(n) for n in fxt_cls_name.split('_')])
    
    def set_id(self):
        """returns id of this set (the primary key value)."""
        return getattr(self.data, 'id') # id is a magic property in sqlobject, see __init__
    
    def understand_columns(self):
        """get an understanding of what columns are what, foreign keys, etc."""
        from sqlobject.col import SOForeignKey
        
        for name,col in self.meta.columns.items():
            if isinstance(col, SOForeignKey):
                self.foreign_key_class[col.name] = col.foreignKey
                
#### I don't know if this is necessary anymore...

# if sqlobject:
#     # OUCH!
#     # prepare for sqlobject monkey patch :( ...
#     # this is so that foreign key lookups work right when 
#     # there are multiple schemas having the same table 
#     # (perfectly legal, but sqlobject was only finding the primary key 
#     # from the first schema)
#     import re
#     def columnsFromSchema(self, tableName, soClass):
# 
#         keyQuery = """
#         SELECT pg_catalog.pg_get_constraintdef(oid) as condef
#         FROM pg_catalog.pg_constraint r
#         WHERE r.conrelid = %s::regclass AND r.contype = 'f'"""
# 
#         colQuery = """
#         SELECT a.attname,
#         pg_catalog.format_type(a.atttypid, a.atttypmod), a.attnotnull,
#         (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d
#         WHERE d.adrelid=a.attrelid AND d.adnum = a.attnum)
#         FROM pg_catalog.pg_attribute a
#         WHERE a.attrelid =%s::regclass
#         AND a.attnum > 0 AND NOT a.attisdropped
#         ORDER BY a.attnum"""
#     
#         # kumar: add limit 1 to get primary key for 
#         # first rel in schema search path
#         primaryKeyQuery = """
#         SELECT pg_index.indisprimary,
#             pg_catalog.pg_get_indexdef(pg_index.indexrelid)
#         FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
#             pg_catalog.pg_index AS pg_index
#         WHERE c.relname = %s
#             AND c.oid = pg_index.indrelid
#             AND pg_index.indexrelid = c2.oid
#             AND pg_index.indisprimary
#         LIMIT 1
#         """
# 
#         keyData = self.queryAll(keyQuery % self.sqlrepr(tableName))
#         keyRE = re.compile(r"\((.+)\) REFERENCES (.+)\(")
#         keymap = {}
# 
#         for (condef,) in keyData:
#             match = keyRE.search(condef)
#             if match:
#                 field, reftable = match.groups()
#                 keymap[field] = reftable.capitalize()
# 
#         primaryData = self.queryAll(primaryKeyQuery % self.sqlrepr(tableName))
#         primaryRE = re.compile(r'CREATE .*? USING .* \((.+?)\)')
#         primaryKey = None
#         for isPrimary, indexDef in primaryData:
#             match = primaryRE.search(indexDef)
#             assert match, "Unparseable contraint definition: %r" % indexDef
#             assert primaryKey is None, "Already found primary key (%r), then found: %r" % (primaryKey, indexDef)
#             primaryKey = match.group(1)
#         assert primaryKey, "No primary key found in table %r" % tableName
#         if primaryKey.startswith('"'):
#             assert primaryKey.endswith('"')
#             primaryKey = primaryKey[1:-1]
# 
#         colData = self.queryAll(colQuery % self.sqlrepr(tableName))
#         results = []
#         if self.unicodeCols:
#             client_encoding = self.queryOne("SHOW client_encoding")[0]
#         for field, t, notnull, defaultstr in colData:
#             if field == primaryKey:
#                 continue
#             colClass, kw = self.guessClass(t)
#             if self.unicodeCols and colClass == col.StringCol:
#                 colClass = col.UnicodeCol
#                 kw['dbEncoding'] = client_encoding
#             kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
#             kw['dbName'] = field
#             kw['notNone'] = notnull
#             if defaultstr is not None:
#                 kw['default'] = self.defaultFromSchema(colClass, defaultstr)
#             elif not notnull:
#                 kw['default'] = None
#             if keymap.has_key(field):
#                 kw['foreignKey'] = keymap[field]
#             results.append(colClass(**kw))
#         return results
#     from sqlobject.postgres import pgconnection
#     from warnings import warn
#     warn("monkey patching %s for multiple schema support" % (
#                     pgconnection.PostgresConnection.columnsFromSchema))
#     pgconnection.PostgresConnection.columnsFromSchema = columnsFromSchema