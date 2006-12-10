
"""utilities for deriving names from datasets."""

class ChainableStyle(type):
    def __add__(orig_style, other_style):
        class ChainedStyles(object):
            __metaclass__ = ChainableStyle
            def translate(self, name):
                return other_style.translate(orig_style.translate(name))
        return ChainedStyles

class DefaultStyle(object):
    """utility for deriving names from datasets.
    
    default is to return all names in original form.
    """
    __metaclass__ = ChainableStyle
    
    def translate(self, name):
        return name

class ClassToAttrStyle(DefaultStyle):
    """derives lower case, underscored names from camel case class names.
    
    i.e. EmployeeData translates to employee_data
    """
    def translate(self, name):
        return camel_to_under(name)

class ConfigurableStyle(DefaultStyle):
    """derives names from datasets with configurable prefixes/suffixes.
    """
    def __init__(self, dataset, prefix=None, suffix=None):
        DefaultStyle.__init__(self, dataset)
        self.prefix = prefix
        self.suffix = suffix
    
    def translate(self, name):
        def assert_s(s, name_contains):
            assert name_contains(s), (
                "%s expected that '%s' %s '%s'" % (
                                self, name, name_contains.__name__, s))
        if self.prefix:
            assert_s(self.prefix, name.startswith)
            name = name[len(self.prefix):]
        if self.suffix:
            assert_s(self.suffix, name.endswith)
            name = name[0:-len(self.suffix)]
        
        return name

class NamedDataStyle(ConfigurableStyle):
    """derives names from datasets assuming Data as a suffix.
    
    i.e. EmployeeData translates to Employee
    """
    def __init__(self, dataset):
        ConfigurableStyle.__init__(self, dataset, suffix='Data')

def camel_to_under(s):
    chunks = []
    chkid = None
    def newchunk():
        chunks.append('')
        return len(chunks)-1
    for ltr in s:
        if ord(ltr) < 97:
            # capital letter :
            chkid = newchunk()
        if chkid is None:
            chkid = newchunk()
            
        chunks[chkid] = chunks[chkid] + ltr
    return '_'.join([c.lower() for c in chunks])