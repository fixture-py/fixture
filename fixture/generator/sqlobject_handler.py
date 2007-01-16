
"""fixture generators for SQLObjects"""

from fixture.style import camel_to_under
from fixture.generator import (
    DataHandler, FixtureSet, register_handler, code_str, 
    UnsupportedHandler, MisconfiguredHandler, )
            
try:
    import sqlobject
except ImportError:
    sqlobject = None

class SQLObjectHandler(DataHandler):
    
    def __init__(self, *a,**kw):
        DataHandler.__init__(self, *a,**kw)
        from sqlobject import sqlhub, connectionForURI
        if self.options.dsn:
            self.connection = connectionForURI(self.options.dsn)
        else:
            raise MisconfiguredHandler(
                    "--dsn option is required by %s" % self.__class__)
    
    def begin(self):
        """called once when starting to build a fixture.
        """
        self.add_import('from datetime import datetime')
        self.add_import('from testtools.fixtures import SOFixture')
    
    def find(self, idval):
        self.rs = [self.obj.get(idval)]
        
    def findall(self, query):
        """gets record set for query."""        
        self.rs = self.obj.select(query, connection=self.connection)
    
    def fxt_type(self):
        return 'SOFixture'
    
    def meta(self, fxt_kls):
        """returns list of lines to add to the fixture class's meta.
        """
        return ["so_class = %s" % fxt_kls]
    
    def mk_key(self, fset):
        """return a unique key for this fixture set.
        
        this is the so class name + primary key value
        """
        so_class = fset.obj_id()
        return "_".join(str(s) for s in (
                        self.mk_var_name(so_class), fset.set_id()))
    
    def mk_var_name(self, fxt_cls_name):
        """returns a variable name for the instance of the fixture class.
        """
        return "_".join([camel_to_under(n) for n in fxt_cls_name.split('_')])
    
    @staticmethod
    def recognizes(object_path, obj=None):
        """returns True if obj is a SQLObject class.
        """
        if obj is None:
            return False
        if not sqlobject:
            raise UnsupportedHandler("sqlobject module not found")
        from sqlobject.declarative import DeclarativeMeta
        if type(obj) is DeclarativeMeta and obj.__name__ not in (
                        'SQLObject', 'sqlmeta', 'ManyToMany', 'OneToMany'):
            return True
    
    def resolve_data_dict(self, fset):
        """given a fixture set, resolve the linked sets
        in the data_dict and log any necessary headers.
        
        return the data_dict
        """
        # need to clean header per resolution. hmm
        self.data_header = []
        self.add_data_header('r = self.meta.req')
        
        def add_import_class(so_class=None):
            from sqlobject.classregistry import findClass
            if not so_class:
                so_class = fset.obj_id()
            kls = findClass(so_class)
            # this probably isn't very flexible ...
            self.add_import("from %s import %s" % (
                                kls.__module__, so_class))
        add_import_class()
        
        for k,v in fset.data_dict.items():
            if isinstance(v, FixtureSet):
                # then it's a foreign key link
                linked_fset = v
                meta = linked_fset.meta
                so_class = linked_fset.obj_id()
                add_import_class(so_class)
                fxt_class = self.mk_class_name(so_class)
                fxt_var = self.mk_var_name(so_class)
                self.add_data_header("r.%s = %s()" % (
                                            fxt_var, 
                                            fxt_class))
                fset.data_dict[k] = code_str("r.%s.%s.%s" % (
                                            fxt_var, 
                                            self.mk_key(linked_fset),
                                            meta.style.idForTable(meta.table)))
        return fset.data_dict
    
    def sets(self):
        """yields FixtureSet for each row in SQLObject."""
        for row in self.rs:
            yield SQLObjectFixtureSet(row, self.obj, connection=self.connection)
            
register_handler(SQLObjectHandler)

class SQLObjectFixtureSet(FixtureSet):
    """a fixture set for a SQLObject row."""
    
    def getDbName(self, col):
        if col.dbName is not None:
            return col.dbName
        else:
            return self.meta.style.pythonAttrToDBColumn(col.name)
    
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
        cols.extend([self.getDbName(c) for c in self.meta.columnList])
    
        vals = [getattr(self.data, self.meta.idName)]
        vals.extend([self.get_col_value(c.name) for c in self.meta.columnList])
    
        self.data_dict = dict(zip(cols, vals))
    
    def obj_id(self):
        """returns id of this data object (the model name)."""
        return self.model.__name__
    
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
    
    def set_id(self):
        """returns id of this set (the primary key value)."""
        return getattr(self.data, self.meta.idName)
    
    def understand_columns(self):
        """get an understanding of what columns are what, foreign keys, etc."""
        from sqlobject.col import SOForeignKey
        
        for name,col in self.meta.columns.items():
            if isinstance(col, SOForeignKey):
                #dbcol = self.meta.style.pythonAttrToDBColumn(col.name)
                self.foreign_key_class[col.name] = col.foreignKey
                

if sqlobject:
    # OUCH!
    # prepare for sqlobject monkey patch :( ...
    # this is so that foreign key lookups work right when 
    # there are multiple schemas having the same table 
    # (perfectly legal, but sqlobject was only finding the primary key 
    # from the first schema)
    import re
    def columnsFromSchema(self, tableName, soClass):

        keyQuery = """
        SELECT pg_catalog.pg_get_constraintdef(oid) as condef
        FROM pg_catalog.pg_constraint r
        WHERE r.conrelid = %s::regclass AND r.contype = 'f'"""

        colQuery = """
        SELECT a.attname,
        pg_catalog.format_type(a.atttypid, a.atttypmod), a.attnotnull,
        (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d
        WHERE d.adrelid=a.attrelid AND d.adnum = a.attnum)
        FROM pg_catalog.pg_attribute a
        WHERE a.attrelid =%s::regclass
        AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum"""
    
        # kumar: add limit 1 to get primary key for 
        # first rel in schema search path
        primaryKeyQuery = """
        SELECT pg_index.indisprimary,
            pg_catalog.pg_get_indexdef(pg_index.indexrelid)
        FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
            pg_catalog.pg_index AS pg_index
        WHERE c.relname = %s
            AND c.oid = pg_index.indrelid
            AND pg_index.indexrelid = c2.oid
            AND pg_index.indisprimary
        LIMIT 1
        """

        keyData = self.queryAll(keyQuery % self.sqlrepr(tableName))
        keyRE = re.compile(r"\((.+)\) REFERENCES (.+)\(")
        keymap = {}

        for (condef,) in keyData:
            match = keyRE.search(condef)
            if match:
                field, reftable = match.groups()
                keymap[field] = reftable.capitalize()

        primaryData = self.queryAll(primaryKeyQuery % self.sqlrepr(tableName))
        primaryRE = re.compile(r'CREATE .*? USING .* \((.+?)\)')
        primaryKey = None
        for isPrimary, indexDef in primaryData:
            match = primaryRE.search(indexDef)
            assert match, "Unparseable contraint definition: %r" % indexDef
            assert primaryKey is None, "Already found primary key (%r), then found: %r" % (primaryKey, indexDef)
            primaryKey = match.group(1)
        assert primaryKey, "No primary key found in table %r" % tableName
        if primaryKey.startswith('"'):
            assert primaryKey.endswith('"')
            primaryKey = primaryKey[1:-1]

        colData = self.queryAll(colQuery % self.sqlrepr(tableName))
        results = []
        if self.unicodeCols:
            client_encoding = self.queryOne("SHOW client_encoding")[0]
        for field, t, notnull, defaultstr in colData:
            if field == primaryKey:
                continue
            colClass, kw = self.guessClass(t)
            if self.unicodeCols and colClass == col.StringCol:
                colClass = col.UnicodeCol
                kw['dbEncoding'] = client_encoding
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            kw['dbName'] = field
            kw['notNone'] = notnull
            if defaultstr is not None:
                kw['default'] = self.defaultFromSchema(colClass, defaultstr)
            elif not notnull:
                kw['default'] = None
            if keymap.has_key(field):
                kw['foreignKey'] = keymap[field]
            results.append(colClass(**kw))
        return results
    from sqlobject.postgres import pgconnection
    pgconnection.PostgresConnection.columnsFromSchema = columnsFromSchema