
"""fixture generators for SQLObjects"""

from fixture.generator.generator import (
            GeneratorHandler, FixtureSet, register_handler)

class SOGeneratorHandler(GeneratorHandler):
    def findall(self, query=None):
        """gets record set for params."""
        
        ## was before ...
        # if query is not None:
        #     rs = model.select(query, clauseTables=clauseTables, 
        #                                         orderBy=orderBy)
        # else:
        #     rs = model.select(orderBy=orderBy)
        # if show_query_only:
        #     print rs

        self.rs = self.obj.select(query)
    
    @staticmethod
    def recognizes(obj):
        """returns True if obj is a SQLObject class.
        """
        from sqlobject.declarative import DeclarativeMeta
        if type(obj) is DeclarativeMeta and obj.__name__ not in (
                        'SQLObject', 'sqlmeta', 'ManyToMany', 'OneToMany'):
            return True
    
    def sets(self):
        """yields FixtureSet for each row in SQLObject."""
        for row in self.rs:
            yield SOFixtureSet(row, self.obj)
            
register_handler(SOGeneratorHandler)

class SOFixtureSet(FixtureSet):
    """a fixture set for a SQLObject row."""
    
    def getDbName(self, col):
        if col.dbName is not None:
            return col.dbName
        else:
            return self.meta.style.pythonAttrToDBColumn(col.name)
    
    def __init__(self, row, model):
        FixtureSet.__init__(self, row)
        self.model = model
        self.meta = model.sqlmeta
        self.fkey_dict = {}
        self.primary_key = None
        
        self.understand_columns()
    
        cols = [self.meta.style.idForTable(self.meta.table)]
        cols.extend([self.getDbName(c) for c in self.meta.columnList])
    
        vals = [row.id]
        vals.extend([getattr(row, c.name) for c in self.meta.columnList])
    
        self.data_dict = dict(zip(cols, vals))
    
    def understand_columns(self):
        """get an understanding of what columns are what, foreign keys, etc."""
        from sqlobject.col import SOForeignKey
        
        # fkeys = [] # fkeys in order of appearance
        # fkey_idmap = {} # col.name : list of ids
        # fkey_classmap = {}
        
        for name,col in self.meta.columns.items():
            if isinstance(col, SOForeignKey):
                dbcol = self.meta.style.pythonAttrToDBColumn(col.name)
                self.fkey_dict[dbcol] = col.foreignKey
                
                
# OUCH! refactor me (code in genfix and genmodel)
# prepare for sqlobject monkey patch :( ...
# this is so that foreign key lookups work right when 
# there are multiple schemas having the same table 
# (perfectly legal, but sqlobject only finds the first primary key)
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
