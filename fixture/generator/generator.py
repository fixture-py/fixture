#!/usr/bin/env python

"""query real data sources and generate python code to load that data.
"""

import sys
import os
import optparse
import inspect
import pprint
handler_registry = []

class code_str(str):
    """string that reproduces without quotes.
    
    """
    def __repr__(self):
        return str.__repr__(self)[1:-1]

class FixtureCache(object):
    """cache of Fixture objects and their data sets to be generatred.
    
    needs to store resulting fixture object with set IDs so that
    foreign key data can accumulate without duplication.
    
    For example, if we have a product set that requires category foo 
    and an offer set that requires category foo, the second one loaded 
    needs to acknowledge that foo is already loaded and needs to obtain 
    the key to that fixture too, to generate the right link.
    """
    def __init__(self):
        self.registry = {}
        self.order_of_appearence = []
    
    def add(self, set):
        fxtid = set.obj_id()        
        self.push_fxtid(fxtid)
        if not self.registry.has_key(fxtid):
            self.registry[fxtid] = {}
        
        # we want to add a new set but
        # MERGE in the data if the set exists.
        # this merge is done assuming that sets of
        # the same id will always be identical 
        # (which should be true for db fixtures)
        self.registry[fxtid][set.set_id()] = set
    
    def push_fxtid(self, fxtid):
        o = self.order_of_appearence
        # keep pushing names, but keep the list unique...
        try:
            o.remove(fxtid)
        except ValueError:
            pass
        o.append(fxtid)

class FixtureGenerator(object):
    """produces a callable object that can generate fixture code.
    """
    basemeta_tpl = """
class basemeta:
    pass"""
    
    fixture_class_tpl = """
class %(fxt_class)s(%(fxt_type)s):
    class meta(basemeta):
        %(meta)s
    def data(self):
        %(data_header)s
        return %(data)s"""
        
    def __init__(self, query=None):
        self.handler = None
        self.query = query
        self.cache = FixtureCache()
    
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
    
    def code(self):
        """buidls and returns code string.
        """
        tpl = {'fxt_type': self.handler.fxt_type()}
        
        code = [self.basemeta_tpl]
        o = [k for k in self.cache.order_of_appearence]
        o.reverse()
        for kls in o:
            tpl['data'] = []
            tpl['fxt_class'] = self.handler.mk_class_name(kls)
            tpl['meta'] = "\n        ".join(self.handler.meta(kls))
            
            val_dict = self.cache.registry[kls]
            for k,fset in val_dict.items():
                key = self.handler.mk_key(fset)
                data = self.handler.resolve_data_dict(fset)
                tpl['data'].append((key, data))
                
            tpl['data_header'] = "\n        ".join(
                                    self.handler.data_header) + "\n"
            tpl['data'] = pprint.pformat(tuple(tpl['data']))
            code.append(self.fixture_class_tpl % tpl)
            
        code = "\n".join(self.handler.import_header + code)
        return code
    
    def __call__(self, obj):
        """uses data obj to generate code for a fixture.
    
        returns code string.
        """
        self.handler = self.get_handler(obj)
        self.handler.findall(query=self.query)
        
        # need to loop through all sets,
        # then through all set items and add all sets of all 
        # foreign keys and their foreign keys.
        # got it???
        
        self.handler.begin()
        def cache_set(s):        
            self.cache.add(s)
            for (k,v) in s.data_dict.items():
                if isinstance(v, FixtureSet):
                    f_set = v
                    cache_set(f_set)
        for s in self.handler.sets():
            cache_set(s)
        
        return self.code()

def register_handler(handler):
    handler_registry.append(handler)

class FixtureSet(object):
    """a key, data_dict pair for a set in a fixture.
    
    takes a data attribute which must be understood by the concrete FixtureSet
    """
    
    def __init__(self, data):
        self.data = data
        self.data_dict = {}
    
    def __repr__(self):
        return "<%s at %s for data %s>" % (
                self.__class__.__name__, hex(id(self)), 
                pprint.pformat(self.data_dict))
    
    def obj_id(self):
        """returns a unique value that identifies the object used
        to generate this fixture.
        
        i.e. typically, this is the name of the data model, say Employees
        """
        raise NotImplementedError
    
    def set_id(self):
        """returns a unique value that identifies this set
        within its class.
        
        i.e. primary key for the row
        """
        raise NotImplementedError

class DataHandler(object):
    """handles an object that can provide fixture data.
    """
    def __init__(self, obj, prefix="", suffix="Data"):
        self.obj = obj
        self.data_header = [] # vars at top of data() method
        self.import_header = [] # lines of import statements
        self.imports = [] # imports to put at top of file
        self.prefix = prefix
        self.suffix = suffix
    
    def add_data_header(self, hdr):
        if hdr not in self.data_header:
            self.data_header.append(hdr)
    
    def add_import(self, _import):
        if _import not in self.import_header:
            self.import_header.append(_import)
    
    def begin(self):
        """called once when starting to build a fixture.
        """
        raise NotImplementedError
    
    def find(self, idval):
        """finds a record set based on key, idval."""
        raise NotImplementedError
    
    def findall(self, query):
        """finds all records based on parameters."""
        raise NotImplementedError
    
    def fxt_type(self):
        """returns name of the type of Fixture class for this data object."""
    
    def meta(self, fxt_kls):
        """returns list of lines to add to the fixture class's meta.
        """
        return ['pass']
    
    def mk_class_name(self, obj_name):
        """returns a fixture class for the data object name.
        """
        # maybe a style object to do this?
        
        return "%s%s%s" % (self.prefix, obj_name, self.suffix)
        
    def mk_key(self, fset):
        """return a unique key for this fixture set."""
        raise NotImplementedError
    
    def mk_var_name(self, fxt_cls_name):
        """returns a variable name for the instance of the fixture class.
        """
        raise NotImplementedError
    
    @staticmethod
    def recognizes(obj):
        """return True if self can handle this object.
        """
        raise NotImplementedError
        
    def resolve_data_dict(self, fset):
        """make any resolutions to a fixture set's data_dict.
        
        return the data_dict
        """
        raise NotImplementedError
        
    def sets(self):
        """yield a FixtureSet for each set in obj."""
        raise NotImplementedError

def run_generator(argv=sys.argv[1:]):
    """
    Using the data object specified in the path, generate fixture code to 
    reproduce its data.
    """
    parser = optparse.OptionParser(
        usage=('%prog [options] package.path.ObjectName' 
                                    + "\n\n" + inspect.getdoc(run_generator)))
    parser.add_option('-q','--query',
                help="like, \"id = 1705\" ")
    # parser.add_option('--show_query_only', action='store_true',
    #             help="prints out query generated by sqlobject and exits")
    # parser.add_option('-c','--clause_tables', default=[],
    #             help="comma separated list of tables for query")
    # parser.add_option('-l','--limit', type='int',
    #             help="max results to return")
    # parser.add_option('-s','--order_by',
    #             help="orderBy=ORDER_BY")
    parser.add_option('-d','--dsn',
                help="sets db connection")
    
    (options, args) = parser.parse_args(argv)
    try:
        model_path, = args
    except ValueError:
        parser.error('incorrect arguments')
    
    name, model_name = os.path.splitext(model_path)
    if not model_name:
        model = __import__(name, globals(), locals(), [])
    else:
        if model_name.startswith('.'):
            model_name = model_name[1:]
        model = __import__(name, globals(), locals(), [model_name]) 
        model = getattr(model, model_name)
    
    # if options.dsn:
    #     from sqlobject import sqlhub, connectionForURI
    #     sqlhub.processConnection = connectionForURI(options.dsn)
        
    generate = FixtureGenerator(query=options.query)
    return generate(model)

def main():
    print( run_generator())
    return 0

if __name__ == '__main__':
    main()