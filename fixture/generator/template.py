
"""templates that generate fixture modules."""

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
    
    def __repr__(self):
        return "'%s'" % self.__class__.__name__
    
    def header(self):
        raise NotImplementedError
    
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

templates.register(fixture(), default=True)

class testtools(Template):
    """renders Fixture objects for the legacy testtools interface.
    """
    
    fixture = """
class %(fxt_class)s(%(fxt_type)s):
    class meta(metabase):
        %(meta)s
    def data(self):
        %(data_header)s
        return %(data)s"""
    
    def header(self):
        return self.basemeta
    
    def meta(self, fxt_kls):
        """returns list of lines to add to the fixture class's meta.
        """
        return ["so_class = %s" % fxt_kls]
        
templates.register(testtools())