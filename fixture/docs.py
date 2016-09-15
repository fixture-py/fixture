#!/usr/bin/env python

"""fixture documentation utilities
"""

import subprocess
import sys

import re
from docutils import statemachine
from docutils.parsers.rst import directives
from os import path
from six import StringIO


heredir = path.dirname(__file__)
srcdir = path.join(heredir, '..', 'docs')
builddir = path.abspath(path.join(srcdir, '..', 'build'))

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

def shell(  
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    """insert a shell command's raw output in a pre block, like::
        
        | .. shell:: 
        |    :run_on_method: some.module.main
        | 
        |    mycmd --arg 1
    
    Also:
    
        | .. shell::
        |    :setup: some.module.setup
        |    :teardown: some.module.teardown
        | 
        |    mycmd --arg 1
    
    """
    printable_cmd_parts = content
    cmd = ' '.join([c.replace("\\", "") for c in content])
    
    if options.get('setup'):
        setup = get_object_from_path(options['setup'])
        setup()
        
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
        # get args with whitespace normalized:
        for part in re.split(r'\s*', cmd.strip()):
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
            except SystemExit as e:
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
    
    if options.get('teardown'):
        setup = get_object_from_path(options['teardown'])
        setup()
        
    # just create a pre block and fill it with command output...
    pad = "  "
    output = ["\n::\n\n"]
    output.append(pad + "$ " + ("%s\n" % pad).join(printable_cmd_parts) + "\n")
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

shell.arguments = (0, 0, 1)
shell.options = {
    # 'doctest_module_first': str, 
    'setup': str,
    'teardown': str,
    'run_on_method': str}
shell.content = 1

directives.register_directive('shell', shell)

def setup_command_data():
    import os

    if os.path.exists('/tmp/fixture_example.db'):
        os.unlink('/tmp/fixture_example.db')
    if os.path.exists('/tmp/fixture_generate.db'):
        os.unlink('/tmp/fixture_generate.db')
    
    import sqlalchemy as sa
    from sqlalchemy import orm
    from fixture.examples.db.sqlalchemy_examples import (
                                    Author, authors, Book, books, metadata)
    metadata.bind = sa.create_engine('sqlite:////tmp/fixture_example.db')
    metadata.create_all()
    orm.mapper(Book, books)
    orm.mapper(Author, authors, properties={'books': orm.relation(Book, backref='author')})
    Session = orm.sessionmaker(bind=metadata.bind, autoflush=True, transactional=True)
    session = Session()

    frank = Author()
    frank.first_name = "Frank"
    frank.last_name = "Herbert"
    session.save(frank)

    dune = Book()
    dune.title = "Dune"
    dune.author = frank
    session.save(dune)

    session.commit()
    
    