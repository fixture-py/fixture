#!/usr/bin/env python

"""generate DataSet classes from real data.

See :ref:`Using the fixture command <using-fixture-command>` for examples.

"""

import inspect
import optparse
import os
import pkg_resources
import sys

from six import with_metaclass

from fixture.command.generate.template import templates, is_template
from warnings import warn


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
    
def register_handler(handler):
    handler_registry.append(handler)

def clear_handlers():
    handler_registry[:] = []

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

class DataSetGenerator(object):
    """produces a callable object that can generate DataSet code.
    """
        
    template = None
        
    def __init__(self, options, template=None):
        self.handler = None
        self.options = options
        self.cache = FixtureCache()
        if template:
            self.template = template
    
    def get_handler(self, object_path, obj=None, importable=True, **kw):
        """find and return a handler for object_path.
        
        any additional keywords will be passed into the handler's constructor
        """            
        handler = None
        for h in handler_registry:
            try:
                recognizes_obj = h.recognizes(object_path, obj=obj)
            except UnsupportedHandler as e:
                warn("%s is unsupported (%s)" % (h, e))
                continue
            if recognizes_obj:
                handler = h(object_path, self.options, 
                            obj=obj, template=self.template, **kw)
                break
        if handler is None:
            raise UnrecognizedObject(
                    "no handler recognizes object %s at %s (importable? %s); "
                    "tried handlers %s" %
                        (obj, object_path, (importable and "YES" or "NO"), 
                            ", ".join([str(h) for h in handler_registry])))
        return handler
    
    def resolve_object_path(self, object_path):
        """resolves an object path
        
        if an object path is importable, returns (True, <object>)
        otherwise, returns (False, None)
        """
        importable = True
        
        path, object_name = os.path.splitext(object_path)
        try:
            if not object_name:
                obj = __import__(path, globals(), locals(), [])
            else:
                if object_name.startswith('.'):
                    object_name = object_name[1:]
                obj = __import__(path, globals(), locals(), [object_name]) 
                obj = getattr(obj, object_name)
        except (ImportError, AttributeError):
            importable = False
            obj = None
        return importable, obj
    
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
    
    def __call__(self, object_path, setup_callbacks=None):
        """uses data obj to generate code for a fixture.
    
        returns code string.
        """
        importable, obj = self.resolve_object_path(object_path)
        # perform setup callbacks here after the object has been imported (above)
        # this is mainly designed for elixir
        if setup_callbacks:
            for setup in setup_callbacks:
                setup()
        self.handler = self.get_handler(object_path, obj=obj, importable=importable)
        self.handler.begin()
        try:
            self.handler.findall(self.options.where)
            def cache_set(s):        
                self.cache.add(s)
                for (k,v) in s.data_dict.items():
                    if isinstance(v, FixtureSet):
                        f_set = v
                        cache_set(f_set)
                        
            # need to loop through all sets,
            # then through all set items and add all sets of all 
            # foreign keys and their foreign keys.
            # got it???
            
            for s in self.handler.sets():
                cache_set(s)
        except:
            self.handler.rollback()
            raise
        else:
            self.handler.commit()
        
        return self.code()

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

class HandlerType(type):
    def __str__(self):
        # split camel class name into something readable?
        return self.__name__


class DataHandler(with_metaclass(HandlerType)):
    """handles an object that can provide fixture data.
    """

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

def dataset_generator(argv):
    """%prog [options] OBJECT_PATH
    
    Using the object specified in the path, generate DataSet classes (code) to 
    reproduce its data.  An OBJECT_PATH can be a python path or a file path
    or anything else that a handler can recognize.
    
    When targetting Python objects the OBJECT_PATH is dot separated.  
    For example, targetting the Employee class in models.py would look like:
    
        directory_app.models.Employee
    
    """
    parser = optparse.OptionParser(
        usage=(inspect.getdoc(dataset_generator)))
    parser.add_option('--dsn',
                help="Sets db connection for a handler that uses a db")
    parser.add_option('-w','--where',
                help="SQL where clause, i.e. \"id = 1705\" ")
        
    d = "Data"
    parser.add_option('--suffix',
        help = (  
            "String suffix for all dataset class names "
            "(default: %s; i.e. an Employee object becomes EmployeeData)" % d),
        default=d)
    parser.add_option('--prefix',
        help="String prefix for all dataset class names (default: None)",
        default="")
    
    parser.add_option('--env',
        help = (
            "Module path to use as an environment for finding objects.  "
            "declaring multiple --env values will be recognized"),
        action='append', default=[])
        
    parser.add_option('--require-egg',
        dest='required_eggs',
        help = (
            "A requirement string to enable importing from a module that was "
            "installed in multi-version mode by setuptools.  I.E. foo==1.0.  "
            "You can repeat this option as many times as necessary."),
        action='append', default=[])
    
    default_tpl = templates.default()
    parser.add_option('--template',
        help="Template to use; choices: %s, default: %s" % (
                        tuple([t for t in templates]), default_tpl),
        default=default_tpl)
    
    parser.add_option("-c", "--connect",
        metavar="FUNCTION_PATH", action="append", default=[],
        help=(  "Path to a function that performs a custom connection, accepting a single "
                "parameter, DSN.  I.E. 'some_module.submod:connect' will be called as connect(DSN).  "
                "Called *after* OBJECT_PATH is imported but *before* any queries are made. "
                "This option can be declared multiple times."))
    parser.add_option("-s", "--setup",
        metavar="FUNCTION_PATH", action="append", default=[],
        help=(  "Path to a function that sets up data objects, accepting no parameters. "
                "I.E. 'some_module.submod:setup_all' will be called as setup_all().  "
                "Called *after* OBJECT_PATH is imported but *before* any queries are made "
                "and *before* connect(DSN) is called. "
                "This option can be declared multiple times."))
        
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
    
    curr_opt, curr_path, setup_callbacks = None, None, None
    try:
        curr_opt = '--connect'
        for path in options.connect:
            curr_path = path
            connect = resolve_function_path(path)
            connect(options.dsn)
        curr_opt = '--setup'
        setup_callbacks = []
        for path in options.setup:
            curr_path = path
            setup_callbacks.append(resolve_function_path(path))
    except ImportError:
        etype, val, tb = sys.exc_info()
        parser.error("%s=%s %s: %s" % (curr_opt, curr_path, etype.__name__, val))
        
    try:
        return get_object_data(object_path, options, setup_callbacks=setup_callbacks)   
    except (MisconfiguredHandler, NoData, UnrecognizedObject):
        etype, val, tb = sys.exc_info()
        parser.error("%s: %s" % (etype.__name__, val))

def resolve_function_path(path):
    if ':' in path:
        mod, obj = path.split(':')
    else:
        mod, obj = path, None
    fn = __import__(mod, globals(),globals(), [obj])
    if obj is not None:
        parts = obj.split('.')
        last_attr = fn
        for p in parts:
            if not hasattr(last_attr, p):
                raise ImportError("attribute %s does not exist in module %s" % (obj, mod))
            last_attr = getattr(last_attr, p)
        fn = last_attr
    return fn

def get_object_data(object_path, options, setup_callbacks=None):
    """query object at object_path and return generated code 
    representing its data
    """
    for egg in options.required_eggs:
        pkg_resources.require(egg)
    generate = DataSetGenerator(options)

    if is_template(options.template):
        generate.template = options.template
    else:
        generate.template = templates.find(options.template)
    return generate(object_path, setup_callbacks=setup_callbacks)

def main(argv=sys.argv[1:]):
    if '__testmod__' in argv:
        # sorry this is all I can think of at the moment :(
        import doctest
        from fixture.test import teardown_examples
        teardown_examples()
        try:
            doctest.testmod()
        finally:
            teardown_examples()
        return
    print( dataset_generator(argv))
    return 0

if __name__ == '__main__':
    main()