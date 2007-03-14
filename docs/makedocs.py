#!/usr/bin/env python

import os, sys
from os import path
import inspect
from docutils.parsers.rst import directives
from docutils.core import publish_file, publish_string, publish_doctree
from docutils.parsers import rst
from docutils.nodes import SparseNodeVisitor
from docutils.readers.standalone import Reader
from docutils.writers.html4css1 import HTMLTranslator, Writer
from docutils import nodes

heredir = path.dirname(__file__)
srcdir = heredir
builddir = path.join(heredir, '..', 'build')

def include_docstring(  
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    """include reStructuredText from a docstring.  use the directive like::
        
        | .. include_docstring:: path.to.module
        | .. include_docstring:: path.to.module:SomeClass
        | .. include_docstring:: path.to.module:SomeClass.method
    
    """
    rawpath = arguments[0]
    parts = rawpath.split(u':')
    if len(parts) > 1:
        modpath, obj = parts
    else:
        modpath = parts[0]
        obj = None
    
    dot = modpath.rfind(u'.')
    if dot != -1:
        fromlist = [str(modpath[dot+1:])]
        mod = str(modpath[:dot])
    else:
        fromlist = []
        mod = str(modpath)
    
    # print mod, fromlist
    mod = __import__(mod, globals(), locals(), fromlist)
    if len(fromlist):
        mod = getattr(mod, fromlist[0])
    if obj:
        if obj.find('.') != -1:
            raise NotImplementedError(
                "todo: need to split the object in a getattr loop")
        obj = getattr(mod, obj)
    else:
        obj = mod
    
    source = inspect.getdoc(obj)
    if source is None:
        raise ValueError("cannot find docstring for %s" % obj)
    return [publish_doctree(source)]

include_docstring.arguments = (1, 0, 0)
include_docstring.options = {}
include_docstring.content = 0

directives.register_directive('include_docstring', include_docstring)

def user():
    docsdir = path.join(builddir, 'docs')
    if not path.exists(docsdir):
        os.mkdir(docsdir)
    
    basename = 'index'
    body = publish_file(open(path.join(srcdir, basename + '.rst'), 'r'),
                destination=open(path.join(docsdir, basename + '.html'), 'w'),
                writer_name='html',
                settings_overrides={'halt_level':2,
                                    'report_level':5})
    print "built user docs to %s" % docsdir

def api():
    from pydoctor.driver import main
    argv = [
        '--html-output=%s/apidocs' % builddir, '--project-name=fixture', 
        '--docformat=restructuredtext',
        '--project-url=http://code.google.com/p/fixture/', '--make-html', 
        '--add-package=fixture', '--verbose']
    
    sys.argv[0] = ['pydoctor'] # for sanity
    main(argv)

def main(argv=sys.argv[1:]):
    def usage():
        print ("usage: %(prog)s\n"
               "       %(prog)s user\n"
               "       %(prog)s api" % dict(prog=path.basename(sys.argv[0])))
        sys.exit(1)
        
    if '-h' in argv or '--help' in argv:
        usage()
    try:
        cmd = argv[0]
        if cmd not in ('api', 'user'):
            usage()
    except IndexError:
        cmd = None
        
    if not path.exists(builddir):
        os.mkdir(builddir)
    if cmd:
        run_cmd = globals()[cmd]
        run_cmd()
    else:
        api()
        user()
        
if __name__ == '__main__':
    main()