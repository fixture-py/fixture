
"""fixture generators for SQLObjects"""

from fixture.generator.generator import (
            DataHandler, FixtureSet, register_handler, code_str)

class SODataHandler(DataHandler):
    
    def __repr__(self):
        return "<SQLObject DataHandler>"
    
    def find(self, idval):
        self.rs = [self.obj.get(idval)]
        
    def findall(self, query):
        """gets record set for query."""
        
        ## was before ...
        # if query is not None:
        #     rs = model.select(query, clauseTables=clauseTables, 
        #                                         orderBy=orderBy)
        # else:
        #     rs = model.select(orderBy=orderBy)
        # if show_query_only:
        #     print rs
        
        self.rs = self.obj.select(query)
    
    def fxt_type(self):
        return 'SOFixture'
    
    def meta(self, fxt_kls):
        """returns list of lines to add to the fixture class's meta.
        """
        return ["so_class = %s" % fxt_kls]
    
    @staticmethod
    def recognizes(obj):
        """returns True if obj is a SQLObject class.
        """
        from sqlobject.declarative import DeclarativeMeta
        if type(obj) is DeclarativeMeta and obj.__name__ not in (
                        'SQLObject', 'sqlmeta', 'ManyToMany', 'OneToMany'):
            return True
    
    def resolve_data_dict(self, fset):
        """given a fixture set, resolve the linked sets
        in the data_dict and log any necessary headers.
        
        return the data_dict
        """
        # lazy init, per resolution. hmm
        self.data_header = []
        self.add_data_header('r = self.meta.req')
        
        for k,v in fset.data_dict.items():
            if isinstance(v, FixtureSet):
                # then it's a foreign key link
                f_set = v
                meta = f_set.meta
                # FIXME! add data header for import statement
                fxt_class = f_set.fxtid()
                fxt_var = meta.style.pythonAttrToDBColumn(fxt_class)
                self.add_data_header("r.%s = %s()" % (
                                            fxt_var, 
                                            fxt_class))
                fset.data_dict[k] = code_str("r.%s.%s" % (
                                            fxt_var, 
                                            meta.style.idForTable(meta.table)))
        return fset.data_dict
    
    def sets(self):
        """yields FixtureSet for each row in SQLObject."""
        for row in self.rs:
            yield SOFixtureSet(row, self.obj)
            
register_handler(SODataHandler)

class SOFixtureSet(FixtureSet):
    """a fixture set for a SQLObject row."""
    
    def getDbName(self, col):
        if col.dbName is not None:
            return col.dbName
        else:
            return self.meta.style.pythonAttrToDBColumn(col.name)
    
    def __init__(self, data, model):
        FixtureSet.__init__(self, data)
        self.model = model
        self.meta = model.sqlmeta
        self.foreign_key_class = {}
        self.primary_key = None
        
        self.understand_columns()
        
        # NOTE: primary keys are not included in columnList ...
        
        cols = [self.meta.style.idForTable(self.meta.table)]
        cols.extend([self.getDbName(c) for c in self.meta.columnList])
    
        vals = [getattr(self.data, self.meta.idName)]
        vals.extend([self.get_col_value(c.name) for c in self.meta.columnList])
    
        self.data_dict = dict(zip(cols, vals))
    
    def fxtid(self):
        """returns id of this fixture (the class name)."""
        return self.model.__name__
    
    def get_col_value(self, colname):
        """transform column name into a value or a
        new set if it's a foreign key (recursion).
        """
        from sqlobject.classregistry import findClass
        value = getattr(self.data, colname)
        if self.foreign_key_class.has_key(colname):
            model = findClass(self.foreign_key_class[colname])
            rs = model.get(value)
            return SOFixtureSet(rs, model)
        else:
            return value
    
    def setid(self):
        """returns id of this set (the primary key value)."""
        return getattr(self.data, self.meta.idName)
    
    def understand_columns(self):
        """get an understanding of what columns are what, foreign keys, etc."""
        from sqlobject.col import SOForeignKey
        
        for name,col in self.meta.columns.items():
            if isinstance(col, SOForeignKey):
                #dbcol = self.meta.style.pythonAttrToDBColumn(col.name)
                self.foreign_key_class[col.name] = col.foreignKey
                
                
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
    
    # kumar: add limit 1 to get primary key for first rel in schema search path
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
