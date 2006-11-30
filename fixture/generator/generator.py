#!/usr/bin/env python

"""query real data sources and generate python code to load that data.
"""

import sys
import optparse
import pprint
handler_registry = []

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
    def __init__(self, query=None):
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
    
    def __call__(self, obj):
        """uses data obj to generate code for a fixture.
    
        returns code string.
        """
        handler = self.get_handler(obj)
        code = ''
        handler.findall(query=self.query)
        
        # need to loop through all sets,
        # then through all set items and add all sets of all 
        # foreign keys and their foreign keys.
        # got it???
        
        def cache_handler(handler):        
            for s in handler.sets():
                self.cache.add(s)
                for (k,v) in s.data_dict.items():
                    if isinstance(v, GeneratorHandler):
                        f_handler = v
                        # this is sort of lame
                        f_handler.find(f_handler.key_value)
                        cache_handler(f_handler)
        cache_handler(handler)
        
        pprint.pprint( self.cache.order_of_appearence)
        pprint.pprint( self.cache.registry)
        print code
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

class GeneratorHandler(object):
    """handles actual generation of code based on an object.
    """
    def __init__(self, obj, key_value=None):
        self.obj = obj
        self.key_value = key_value
    
    def find(self, idval):
        """finds a record set based on key, idval."""
        raise NotImplementedError
    
    def findall(self, query):
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

def main(argv=sys.argv[1:]):
    return 0

if __name__ == '__main__':
    main()