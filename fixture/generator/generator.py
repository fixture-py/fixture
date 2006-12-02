#!/usr/bin/env python

"""query real data sources and generate python code to load that data.
"""

import sys
import optparse
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
        fxtid = set.fxtid()
        if not self.registry.has_key(fxtid):
            self.order_of_appearence.append(fxtid)
            self.registry[fxtid] = {}
        
        # we want to add a new set but
        # MERGE in the data if the set exists.
        # this merge is done assuming that sets of
        # the same id will always be identical 
        # (which should be true for db fixtures)
        self.registry[fxtid][set.setid()] = set

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
            tpl['fxt_class'] = 'P_%s' % kls
            tpl['meta'] = "\n        ".join(self.handler.meta(kls))
            
            val_dict = self.cache.registry[kls]
            for k,fset in val_dict.items():
                key = "prefix_%s" % k
                data = self.handler.resolve_data_dict(fset)
                tpl['data'].append((key, data))
                
            tpl['data_header'] = "\n        ".join(
                                    self.handler.data_header) + "\n"
            tpl['data'] = pprint.pformat(tuple(tpl['data']))
            code.append(self.fixture_class_tpl % tpl)
            
        code = "\n".join(code)
        print code
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
    
    def fxtid(self):
        """returns a unique value that identifies the class used
        to generate this fixture.
        
        i.e. EmployeeData if this were a fixture object for employees
        """
        raise NotImplementedError
    
    def setid(self):
        """returns a unique value that identifies this set
        within its class.
        
        i.e. primary key for the row
        """
        raise NotImplementedError

class DataHandler(object):
    """handles an object that can provide fixture data.
    """
    def __init__(self, obj):
        self.obj = obj
        self.data_header = [] # vars at top of data() method
        self.imports = [] # imports to put at top of file
    
    def add_data_header(self, hdr):
        if hdr not in self.data_header:
            self.data_header.append(hdr)
    
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

def main(argv=sys.argv[1:]):
    return 0

if __name__ == '__main__':
    main()