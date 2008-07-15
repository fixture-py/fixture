
"""Utilities for deriving new names from existing names.

Style objects are used to customize how :ref:`storable objects are found for DataSet objects <using-loadable-fixture-style>`
"""

__all__ = [
    'CamelAndUndersStyle', 'TrimmedNameStyle', 'NamedDataStyle', 
    'PaddedNameStyle', 'ChainedStyle']

class Style(object):
    """
    Utility for deriving new names from existing names.
    
    each method receives a name and returns a new name.
    """
    def __add__(self, newstyle):
        return ChainedStyle(self, newstyle)
        
    def to_attr(self, name):
        """converts name to a new name suitable for an attribute."""
        raise NotImplementedError
    
    def guess_storable_name(self, name):
        """converts a dataset class name to a storage class name."""
        return name
    
    def __repr__(self):
        return "<%s at %s>" % (self.__class__.__name__, hex(id(self)))

class ChainedStyle(Style):
    """
    Combination of two styles, piping first translation 
    into second translation.
    """
    def __init__(self, first_style, next_style):
        self.first_style = first_style
        self.next_style = next_style
    
    def __getattribute__(self, c):
        def assert_callable(attr):
            if not callable(attr):
                raise AttributeError(
                    "%s cannot chain %s" % (self.__class__, attr))
        def chained_call(name):
            f = object.__getattribute__(self, 'first_style')
            first_call = getattr(f, c)
            assert_callable(first_call)
            
            n = object.__getattribute__(self, 'next_style')
            next_call = getattr(n, c)
            assert_callable(next_call)
            
            return next_call(first_call(name))
        return chained_call
    
    def __repr__(self):
        return "%s + %s" % (self.first_style, self.next_style)

class OriginalStyle(Style):
    """
    Style that honors all original names.
    """
    def to_attr(self, name):
        return name
    def guess_storable_name(self, name):
        return name

class CamelAndUndersStyle(Style):
    """
    Style that assumes classes are already in came case 
    but attributes should be underscore separated
    """
    def to_attr(self, name):        
        """
        Derives lower case, underscored names from camel case class names.
    
        i.e. EmployeeData translates to employee_data
        """
        return camel_to_under(name)
    
    def guess_storable_name(self, name):
        """
        Assume a storage name is the same as original.
        
        i.e. Employee becomes Employee
        """
        return name

class TrimmedNameStyle(Style):
    """
    Derives new names from trimming off prefixes/suffixes.
    """
    def __init__(self, prefix=None, suffix=None):
        self.prefix = prefix
        self.suffix = suffix
    
    def _trim(self, name):
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
    
    def to_attr(self, name):
        return self._trim(name)
    
    def guess_storable_name(self, name):
        return self._trim(name)

class PaddedNameStyle(Style):
    """
    Derives new names from padding names with prefixes/suffixes.
    """
    def __init__(self, prefix=None, suffix=None):
        self.prefix = prefix
        self.suffix = suffix
    
    def _pad(self, name):
        if self.prefix:
            name = "%s%s" % (self.prefix, name)
        if self.suffix:
            name = "%s%s" % (name, self.suffix)
        return name
        
    def to_attr(self, name):
        return self._pad(name)
    
    def guess_storable_name(self, name):
        return self._pad(name)

class NamedDataStyle(TrimmedNameStyle):
    """
    Derives names from datasets assuming "Data" as a suffix.
    
    for example, consider this data object and this DataSet::
        
        >>> class Author(object):
        ...     name = None
        ... 
        >>> from fixture import DataSet
        >>> class AuthorData(DataSet):
        ...     class freude:
        ...         name = "Sigmund Freude"
        ... 
    
    if a LoadableFixture is configured with style=NamedDataStyle() then it will 
    automatically look in its env for the object "Author" when loading the 
    DataSet named "AuthorData"
    
    """
    def __init__(self):
        TrimmedNameStyle.__init__(self, suffix='Data')

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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
