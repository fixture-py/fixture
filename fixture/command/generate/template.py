
"""templates that generate fixture modules."""

from fixture.command.generate import code_str
import pprint

def _addto(val, list_):
    if val not in list_:
        list_.append(val)

class _TemplateRegistry(object):
    def __init__(self):
        self.templates = []
        self.lookup = {}
        self._default = None
    
    def __iter__(self):
        for tpl in self.templates:
            yield tpl
    
    def find(self, name):
        return self.templates[self.lookup[name]]
    
    def default(self):
        if self._default is None:
            raise LookupError("no default template has been set")
        return self.templates[self._default]
    
    def register(self, template, default=False):
        name = template.__class__.__name__
        if name in self.lookup:
            raise ValueError("cannot re-register %s with object %s" % (
                                                        name, template))
        self.templates.append(template)
        id = len(self.templates)-1
        self.lookup[name] = id
        
        if default:
            self._default = id
        
templates = _TemplateRegistry()

class Template(object):
    """knows how to render fixture code.
    """
    class dict(dict):
        def __repr__(self):
            s = ["dict("]
            for k,v in self.iteritems():
                s.append("          %s = %s," % (
                                        k, repr(v)))
            s[-1] = s[-1] + ")"
            return "\n".join(s)
    
    class tuple(tuple):
        def __repr__(self):
            s = ["("]
            for item in self:
                s.append("      %s," % repr(item))
            return "\n".join(s) + ")"
            
    class DataDef:
        def __init__(self):
            self.data_header = [] # vars at top of data() method
    
        def add_header(self, hdr):
            if hdr not in self.data_header:
                self.data_header.append(hdr)

        def meta(self, fxt_class):
            """returns list of lines to add to the fixture class's meta.
            """
            return ['pass']
    
    class data(tuple):
        pass
    
    metabase = """
class metabase:
    pass"""
    
    fixture = None
    
    def __init__(self):
        self.import_header = [] # lines of import statements
        self.meta_header = [] # lines of attributes for inner meta class

    def __repr__(self):
        return "'%s'" % self.__class__.__name__
    
    def add_import(self, _import):
        _addto(_import, self.import_header)
    
    def begin(self):
        pass
            
    def header(self, handler):
        return self.metabase
    
    def render(self, tpl):
        if self.fixture is None:
            raise NotImplementedError
        return self.fixture % tpl

def is_template(obj):
    return isinstance(obj, Template)

class fixture(Template):
    """renders DataSet objects for the fixture interface."""
    
    class DataDef(Template.DataDef):
        def __init__(self, *a,**kw):
            Template.DataDef.__init__(self, *a,**kw)
            self.requires = []
    
        def add_reference(self, fxt_class, fxt_var=None):
            _addto(code_str(fxt_class), self.requires)
        
        def fset_to_attr(self, fset, fxt_class):
            # do we need to check for MergedSuperSet ?
            # attribute needs key only
            return code_str("%s.%s.ref(%s)" % (
                        fxt_class, fset.mk_key(), repr(fset.get_id_attr())))
            
        def meta(self, fxt_class):
            return ""
            # if len(self.requires):
            #     return ["requires = %s" % str(tuple(self.requires))]
            # else:
            #     return ["pass"]
    
    fixture = """
class %(fxt_class)s(DataSet):
%(meta)s\
%(data)s"""
    
    metabase = ""
    
    def begin(self):
        self.add_import('import datetime')
        self.add_import("from fixture import DataSet")
    
    class data(object):
        def __init__(self, elements):
            self.elements = elements
        def __repr__(self):
            o = []
            for class_, dict_ in self.elements:
                o.append("    class %s:" % class_)
                for k,v in dict_.iteritems():
                    o.append("        %s = %s" % (k,repr(v)))
            return "\n".join(o)
    
    def header(self, handler):
        return "\n".join(Template.header(self, handler))

templates.register(fixture(), default=True)

class testtools(Template):
    """renders Fixture objects for the legacy testtools interface.
    """
    class DataDef(Template.DataDef):
        def add_reference(self, fxt_class, fxt_var=None):
            self.add_header('r = self.meta.req')
            self.add_header("r.%s = %s()" % (fxt_var, fxt_class))
        
        def fset_to_attr(self, fset, fxt_class):
            return code_str("r.%s.%s.%s" % (
                        fset.mk_var_name(), fset.mk_key(), fset.get_id_attr()))
    
        def meta(self, fxt_class):
            """returns list of lines to add to the fixture class's meta.
            """
            return ["so_class = %s" % fxt_class]
    
    fixture = """
class %(fxt_class)s(%(fxt_type)s):
    class meta(metabase):
        %(meta)s
    def data(self):
        %(data_header)s\
        return %(data)s"""
    
    def begin(self):
        self.add_import('import datetime')
        self.add_import('from testtools.fixtures import SOFixture')
        
templates.register(testtools())