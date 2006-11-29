#!/usr/bin/env python

import sys
import optparse
import pprint
handler_registry = []

class FixtureGenerator(object):
    """produces a callable object that can generate fixture code.
    """
    def __init__(self, query=None):
        self.query = query
    
    def get_handler(self, obj):
        handler = None
        for h in handler_registry:
            if h.recognizes(obj):
                handler = h(obj)
                break
        if handler is None:
            raise ValueError, ("no handler recognizes object %s; tried %s" %
                                (obj, 
                                ", ".join([str(h) for h in handler_registry])))
        return handler
    
    def __call__(self, obj):
        """uses data obj to generate code for a fixture.
    
        returns code string.
        """
        handler = self.get_handler(obj)
        code = ''
        handler.findall(query=self.query)
        
        sets = [s for s in handler.sets()]
        for s in sets:
            print "set:", s
            for subset in s.subsets():
                print "  subset:", subset
    
        return code

def register_handler(handler):
    handler_registry.append(handler)

class FixtureSet(object):
    """a key, data_dict pair for a set in a fixture.
    
    takes a data attribute which must be understood by the concrete FixtureSet
    """
    
    def __init__(self, data):
        self.key = None
        self.data = data
        self.data_dict = {}
    
    def __repr__(self):
        return "<%s '%s' at %s for data %s>" % (
                self.__class__.__name__, self.key, hex(id(self)), 
                pprint.pformat(self.data_dict))
    
    def subsets(self):
        """yields FixtureSets belonging to this FixtureSet.
        
        i.e. foreign keyed rows linked to this row in the database.
        """
        raise NotImplementedError

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
        pass
    
    def subsets(self):
        from sqlobject.col import SOForeignKey
        
        fkeys = [] # fkeys in order of appearance
        fkey_idmap = {} # col.name : list of ids
        fkey_classmap = {}
        
        for name,col in self.meta.columns.items():
            if isinstance(col, SOForeignKey):
                dbcol = self.meta.style.pythonAttrToDBColumn(col.name)
                yield (col.foreignKey, dbcol)

class GeneratorHandler(object):
    """handles actual generation of code based on an object.
    """
    def __init__(self, obj):
        self.obj = obj
    
    def __repr__(self):
        return "<SQLObject handler>"
    
    def findall(self, query=None):
        """finds all records based on parameters."""
        raise NotImplementedError
    
    @staticmethod
    def recognizes(obj):
        """return True if self can handle this object.
        """
        raise NotImplementedError
    
    def sets(self):
        """yield a FixtureSet for each set in obj."""
        raise NotImplementedError

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

def main(argv=sys.argv[1:]):
    return 0

if __name__ == '__main__':
    main()