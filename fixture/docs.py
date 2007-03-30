#!/usr/bin/env python

"""fixture documentation utilities
"""

import os, sys
from os import path
import optparse
import subprocess
import inspect, pydoc, doctest
from docutils import statemachine
from docutils.parsers.rst import directives
from docutils.core import (
    publish_file, publish_string, publish_doctree, publish_from_doctree)
from docutils.parsers import rst
from docutils.nodes import SparseNodeVisitor
from docutils.readers.standalone import Reader
from docutils.writers.html4css1 import HTMLTranslator, Writer
from docutils import nodes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
    
state_is_api = False

def get_object_from_path(rawpath):
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
    return obj

def include_docstring(  
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    """include reStructuredText from a docstring.  use the directive like:
        
        | .. include_docstring:: path.to.module
        | .. include_docstring:: path.to.module:SomeClass
        | .. include_docstring:: path.to.module:SomeClass.method
    
    """
    rawpath = arguments[0]
    obj = get_object_from_path(rawpath)
    source = inspect.getdoc(obj)
    if hasattr(obj, '__module__'):
        mod = obj.__module__
    else:
        mod = obj # big assumption :/
    doctest.run_docstring_examples(source, mod.__dict__)
    if source is None:
        raise ValueError("cannot find docstring for %s" % obj)
    summary, body = pydoc.splitdoc(source)
    
    # nabbed from docutils.parsers.rst.directives.misc.include
    include_lines = statemachine.string2lines(body, convert_whitespace=1)
    state_machine.insert_input(include_lines, None)
    return []
    # return [publish_doctree(body)]

include_docstring.arguments = (1, 0, 0)
include_docstring.options = {}
include_docstring.content = 0

directives.register_directive('include_docstring', include_docstring)

def api_only(
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    """only include a block of rst if generating API documentation."""
    if state_is_api:
        include_lines = statemachine.string2lines("\n".join(content),
                                            convert_whitespace=1)
        state_machine.insert_input(include_lines, None)
    return []

api_only.arguments = (0, 0, 0)
api_only.options = {}
api_only.content = 1
directives.register_directive('api_only', api_only)


def shell(  
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    """insert a shell command's raw output in a pre block, like::
        
        | .. shell:: mycmd --arg 1
    
    """
    cmd = arguments[0]
    # if options.get('doctest_module_first'):
    #     obj = get_object_from_path(options['doctest_module_first'])
    #     import doctest
    #     doctest.testmod(obj, globs=globals())
    if options.get('run_on_method'):
        main = get_object_from_path(options['run_on_method'])
        
        def decode(s):
            if isinstance(s, unicode):
                s = str(s.decode())
            return s
        def unquot(s):
            if s[0] in ('"', "'"):
                s = s[1:-1]
            return s
        cmdlist = []
        for part in cmd.split(' '):
            part = decode(part)
            part = unquot(part)
            e = part.find('=')
            if e != -1:
                # i.e. --where="title='Dune'"
                part = "%s=%s" % (part[:e], unquot(part[e+1:]))
            cmdlist.append(part)
        
        stdout = StringIO()
        stderr = StringIO()
        sys.stdout = stdout
        sys.stderr = stderr
        _program = sys.argv[0]
        sys.argv[0] = cmdlist[0]
        try:
            try:
                main(cmdlist[1:])
            except SystemExit, e:
                returncode = e.code
            else:
                returncode = 0
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            stdout.seek(0)
            stderr.seek(0)
            sys.argv[0] = _program
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, close_fds=True, shell=True)
    
        returncode = p.wait()
        stdout, stderr = p.stdout, p.stderr
        
    if returncode != 0:
        raise RuntimeError("%s\n%s (exit: %s)" % (
                            stderr.read(), cmd, returncode))
    
    # just create a pre block and fill it with command output...
    pad = "  "
    output = ["\n::\n\n"]
    output.append(pad + "$ " + cmd + "\n")
    while 1:
        line = stdout.readline()
        if not line:
            break
        output.append(pad + line)
    output.append("\n")
    
    output = "".join(output)
        
    include_lines = statemachine.string2lines(output)
    state_machine.insert_input(include_lines, None)
    return []

shell.arguments = (1, 0, 1)
shell.options = {
    # 'doctest_module_first': str, 
    'run_on_method': str}
shell.content = 0

directives.register_directive('shell', shell)
    