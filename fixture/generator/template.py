
"""templates that generate fixture modules."""

from fixture.generator import code_str

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
    
    basemeta = """
class metabase:
    pass"""
    
    fixture = None
    
    def __init__(self):
        self.import_header = [] # lines of import statements

    def __repr__(self):
        return "'%s'" % self.__class__.__name__
    
    class DataDef:
        def __init__(self):
            self.data_header = [] # vars at top of data() method
    
        def add_header(self, hdr):
            if hdr not in self.data_header:
                self.data_header.append(hdr)
    
    def add_import(self, _import):
        if _import not in self.import_header:
            self.import_header.append(_import)
            
    def header(self):
        return self.basemeta
    
    def meta(self, fxt_kls):
        """returns list of lines to add to the fixture class's meta.
        """
        return ['pass']
    
    def render(self, tpl):
        if self.fixture is None:
            raise NotImplementedError
        return self.fixture % tpl

def is_template(obj):
    return isinstance(obj, Template)

class fixture(Template):
    """renders DataSet objects for the fixture interface."""
    
    fixture = """
class %(fxt_class)s(DataSet):
    class Meta(metabase):
        %(meta)s
    def data(self):
        %(data_header)s
        return %(data)s"""
    
    def header(self):
        return Template.header(self)

templates.register(fixture(), default=True)

class testtools(Template):
    """renders Fixture objects for the legacy testtools interface.
    """
    class DataDef(Template.DataDef):
        def add_reference(self, fxt_class, fxt_var=None):
            self.add_header('r = self.meta.req')
            self.add_header("r.%s = %s()" % (fxt_var, fxt_class))
        
        def fset_to_attr(self, fset):
            return code_str("r.%s.%s.%s" % (
                        fset.mk_var_name(), fset.mk_key(), fset.get_id_attr()))
    
    fixture = """
class %(fxt_class)s(%(fxt_type)s):
    class meta(metabase):
        %(meta)s
    def data(self):
        %(data_header)s
        return %(data)s"""
    
    def meta(self, fxt_kls):
        """returns list of lines to add to the fixture class's meta.
        """
        return ["so_class = %s" % fxt_kls]
        
templates.register(testtools())