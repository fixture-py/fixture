#!/usr/bin/env python

import sys
import optparse

def generate_fixture(obj, query=None):
    """uses obj and params to generate code for a fixture.
    
    returns code string.
    """
    pass

handler_registry = []
def register_handler(handler):
    handler_registry.append(handler)

class FixtureSet(object):
    """a key, dict pair for a set in a fixture."""
    key = None
    data ={}

class GeneratorHandler(object):
    """handles actual generation of code based on an object.
    """
    def __init__(self, obj):
        self.obj = obj
    
    def __iter__(self):
        """yield a FixtureSet for each set in obj."""
        raise NotImplementedError
    
    @staticmethod
    def can_handle_object(obj):
        """return True if self can handle this object.
        """
        raise NotImplementedError

class SOGeneratorHandler(GeneratorHandler):
    @staticmethod
    def can_handle_object(obj):
        """returns True if obj is a SQLObject class.
        """
        from sqlobject.declarative import DeclarativeMeta
        if type(obj) is DeclarativeMeta and name not in (
                        'SQLObject', 'sqlmeta', 'ManyToMany', 'OneToMany'):
            return True
            
register_handler(SOGeneratorHandler)

def main(argv=sys.argv[1:]):
    return 0

if __name__ == '__main__':
    main()