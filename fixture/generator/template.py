
"""templates that generate fixture modules."""


class MetaStyleFixture(object):
    """template to render Fixture objects that use meta containers.
    """
    
    basemeta = """
class basemeta:
    pass"""
    
    fixture = """
class %(fxt_class)s(%(fxt_type)s):
    class meta(basemeta):
        %(meta)s
    def data(self):
        %(data_header)s
        return %(data)s"""
    
    def header(self):
        return self.basemeta
    
    def render(self, tpl):
        return self.fixture % tpl