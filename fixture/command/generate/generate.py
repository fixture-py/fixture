#!/usr/bin/env python

"""query real data sources and generate python code to load that data.
"""

import sys
import os
import optparse
import inspect
from warnings import warn
from fixture.command.generate.template import templates, is_template
handler_registry = []

class NoData(LookupError):
    """no data was returned by a query"""
    pass
class HandlerException(Exception):
    pass
class UnrecognizedObject(HandlerException):
    pass
class UnsupportedHandler(HandlerException):
    pass
class MisconfiguredHandler(HandlerException):
    pass

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
        
    template = None
        
    def __init__(self, options):
        self.handler = None
        self.options = options
        self.cache = FixtureCache()
    
    def get_handler(self, object_path):
        
        importable = 'YES'
        
        path, object_name = os.path.splitext(object_path)
        try:
            if not object_name:
                obj = __import__(path, globals(), locals(), [])
            else:
                if object_name.startswith('.'):
                    object_name = object_name[1:]
                obj = __import__(path, globals(), locals(), [object_name]) 
                obj = getattr(obj, object_name)
        except ImportError:
            importable = 'NO'            
            obj = None
            
        handler = None
        for h in handler_registry:
            try:
                recognizes_obj = h.recognizes(object_path, obj=obj)
            except UnsupportedHandler, e:
                warn("%s is unsupported (%s)" % (h, e))
                continue
            if recognizes_obj:
                handler = h(object_path, self.options, 
                            obj=obj, template=self.template)
                break
        if handler is None:
            raise UnrecognizedObject, (
                    "no handler recognizes object %s at %s (importable? %s); "
                    "tried handlers %s" %
                        (obj, object_path, importable, 
                            ", ".join([str(h) for h in handler_registry])))
        return handler
    
    def code(self):
        """builds and returns code string.
        """
        tpl = {'fxt_type': self.handler.fxt_type()}
        
        code = [self.template.header(self.handler)]
        o = [k for k in self.cache.order_of_appearence]
        o.reverse()
        for kls in o:
            datadef = self.template.DataDef()
            tpl['data'] = []
            tpl['fxt_class'] = self.handler.mk_class_name(kls)
            
            val_dict = self.cache.registry[kls]
            for k,fset in val_dict.items():
                key = fset.mk_key()
                data = self.handler.resolve_data_dict(datadef, fset)
                tpl['data'].append((key, self.template.dict(data)))
                
            tpl['meta'] = "\n        ".join(datadef.meta(kls))
            tpl['data_header'] = "\n        ".join(datadef.data_header) + "\n"
            tpl['data'] = self.template.data(tpl['data'])
            code.append(self.template.render(tpl))
            
        code = "\n".join(self.template.import_header + code)
        return code
    
    def __call__(self, object_path):
        """uses data obj to generate code for a fixture.
    
        returns code string.
        """
        
        self.handler = self.get_handler(object_path)
        self.handler.findall(query=self.options.query)
        
        # need to loop through all sets,
        # then through all set items and add all sets of all 
        # foreign keys and their foreign keys.
        # got it???
        
        self.handler.begin()
        try:
            def cache_set(s):        
                self.cache.add(s)
                for (k,v) in s.data_dict.items():
                    if isinstance(v, FixtureSet):
                        f_set = v
                        cache_set(f_set)
            for s in self.handler.sets():
                cache_set(s)
        except:
            self.handler.rollback()
            raise
        else:
            self.handler.commit()
        
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
                
    def attr_to_db_col(self, col):
        """returns a database column name for a fixture set's attribute.
        
        this is only useful for sqlobject in how it wants camel case.
        """
        return col
        
    def get_id_attr(self):
        """returns the name of this set's id attribute.
        
        i.e. "id"
        """
        raise NotImplementedError
    
    def mk_key(self):
        """return a unique key for this fixture set.
        
        i.e. <dataclass>_<primarykey>
        """
        return "_".join(str(s) for s in (
                        self.mk_var_name(), self.set_id()))
    
    def mk_var_name(self):
        """returns a variable name for the instance of the fixture class.
        """
        return self.obj_id()
    
    def obj_id(self):
        """returns a unique value that identifies the object used
        to generate this fixture.
        
        by default this is the name of the data model, i.e. Employees
        """
        return self.model.__name__
    
    def set_id(self):
        """returns a unique value that identifies this set
        within its class.
        
        i.e. primary key for the row
        """
        raise NotImplementedError

class Handler(type):
    def __str__(self):
        # split camel class name into something readable?
        return self.__name__

class DataHandler(object):
    """handles an object that can provide fixture data.
    """
    __metaclass__ = Handler
    loadable_fxt_class = None
        
    def __init__(self, object_path, options, obj=None, template=None):
        self.obj_path = object_path
        self.obj = obj
        self.options = options
        self.template = template
    
    def begin(self):
        """called once when starting to build a fixture.
        """
        self.template.begin()
    
    def commit(self):
        """called after performing any action successfully."""
        pass
    
    def find(self, idval):
        """finds a record set based on key, idval."""
        raise NotImplementedError
    
    def findall(self, query):
        """finds all records based on parameters."""
        raise NotImplementedError
    
    def fxt_type(self):
        """returns name of the type of Fixture class for this data object."""
    
    def mk_class_name(self, name_or_fset):
        """returns a fixture class for the fixture set.
        """
        if isinstance(name_or_fset, FixtureSet):
            obj_name = name_or_fset.obj_id()
        else:
            obj_name = name_or_fset
        return "%s%s%s" % (self.options.prefix, obj_name, self.options.suffix)
    
    @staticmethod
    def recognizes(object_path, obj):
        """return True if self can handle this object_path/object.
        """
        raise NotImplementedError        
    
    def resolve_data_dict(self, datadef, fset):
        """given a fixture set, resolve the linked sets
        in the data_dict and log any necessary headers.
        
        return the data_dict
        """        
        self.add_fixture_set(fset)
        
        # this is the dict that defines all keys/vals for
        # the row.  note that the only thing special we 
        # want to do is turn all foreign key values into
        # code strings 
        
        for k,v in fset.data_dict.items():
            if isinstance(v, FixtureSet):
                # then it's a foreign key link
                linked_fset = v
                self.add_fixture_set(linked_fset)
                
                fxt_class = self.mk_class_name(linked_fset)
                datadef.add_reference(  fxt_class,
                                        fxt_var = linked_fset.mk_var_name() )
                fset.data_dict[k] = datadef.fset_to_attr(linked_fset, fxt_class)
                
        return fset.data_dict
    
    def rollback(self):
        """called after any action raises an exception."""
        pass
        
    def sets(self):
        """yield a FixtureSet for each set in obj."""
        raise NotImplementedError

def dataset_generator(argv=sys.argv[1:]):
    """%prog [options] object_path
    
    Using the object specified in the path, generate DataSet classes (code) to 
    reproduce its data.  An object_path can be a python path or a file path
    or anything else that a handler can recognize.
    """
    parser = optparse.OptionParser(
        usage=(inspect.getdoc(dataset_generator)))
    parser.add_option('--dsn',
                help="sets db connection for a handler that uses a db")
    parser.add_option('-q','--query',
                help="like, \"id = 1705\" ")
        
    d = "Data"
    parser.add_option('--suffix',
        help = (  
            "string suffix for all dataset class names "
            "(default: %s; i.e. an Employee object becomes EmployeeData)" % d),
        default=d)
    parser.add_option('--prefix',
        help="string prefix for all dataset class names (default: None)",
        default="")
    
    parser.add_option('--env',
        help = (
            "module path to use as an environment for finding objects.  "
            "declaring multiple --env values will be recognized"),
        action='append', default=[])
    
    default_tpl = templates.default()
    parser.add_option('--template',
        help="template to use; choices: %s, default: %s" % (
                        tuple([t for t in templates]), default_tpl),
        default=default_tpl)
        
    # parser.add_option('--show_query_only', action='store_true',
    #             help="prints out query generated by sqlobject and exits")
    # parser.add_option('-c','--clause_tables', default=[],
    #             help="comma separated list of tables for query")
    # parser.add_option('-l','--limit', type='int',
    #             help="max results to return")
    # parser.add_option('-s','--order_by',
    #             help="orderBy=ORDER_BY")
    
    (options, args) = parser.parse_args(argv)
    try:
        object_path = args[0]
    except IndexError:
        parser.error('incorrect arguments')
    
    try:
        generate = FixtureGenerator(options)
    
        if is_template(options.template):
            generate.template = options.template
        else:
            generate.template = templates.find(options.template)
        return generate(object_path)
    except (MisconfiguredHandler, NoData), e:
        parser.error(e)

def main():
    print( dataset_generator())
    return 0

if __name__ == '__main__':
    main()