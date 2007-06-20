#!/usr/bin/env python

import os, sys, shutil
from os import path
import optparse
from fixture import docs
from fixture.test import teardown_examples
from docutils.core import (
    publish_file, publish_string, publish_doctree, publish_from_doctree)

heredir = path.dirname(__file__)
srcdir = heredir
builddir = path.abspath(path.join(heredir, '..', 'build'))

def build_user():
    """build end-user documentation."""
    docs.state_is_api = False
    docsdir = path.join(builddir, 'docs')
    if not path.exists(docsdir):
        os.mkdir(docsdir)
    
    teardown_examples() # clear tmp files
    stylesheet = path.join(srcdir, 'fixture-docutils.css')
    body = publish_file(open(path.join(srcdir, 'index.rst'), 'r'),
                destination=open(path.join(docsdir, 'index.html'), 'w'),
                writer_name='html',
                settings_overrides={'stylesheet_path': stylesheet},
                # settings_overrides={'halt_level':2,
                #                     'report_level':5}
                )
    f = open(path.join(docsdir, 'index.html'), 'w')
    f.write(body)
    f.close()
    shutil.copy(path.join(srcdir, 'html4css1.css'), 
                path.join(docsdir, 'html4css1.css'))
    shutil.copy(stylesheet, 
                path.join(docsdir, 'fixture-docutils.css'))
    images_target = path.join(docsdir, 'images')
    if path.exists(images_target):
        shutil.rmtree(images_target)
    shutil.copytree(path.join(srcdir, 'images'), images_target)
    print "built user docs to %s" % docsdir

def build_api():
    """build API documentation."""
    docs.state_is_api = True
    from pydoctor.driver import main
    argv = [
        '--html-output=%s/apidocs' % builddir, '--project-name=fixture', 
        '--docformat=restructuredtext',
        '--project-url=http://code.google.com/p/fixture/', '--make-html', 
        '--add-package=fixture', '--verbose', '--verbose']
    
    sys.argv[0] = ['pydoctor'] # for sanity
    main(argv)

def build(argv=sys.argv[1:]):
    """build documentation"""
    global builddir
    p = optparse.OptionParser(usage=(
                      "%prog\n"
               "       %prog user\n"
               "       %prog api"))
    p.add_option('--build-dir', 
        help="create documentation sub-directories here")
    (options, args) = p.parse_args(argv)
    try:
        cmd = args[0]
    except IndexError:
        cmd = None
    else:
        if cmd not in ('api', 'user'):
            p.error("unrecognized command")
    
    if options.build_dir:
        builddir = options.build_dir
    if not path.exists(builddir):
        os.mkdir(builddir)
    if cmd:
        run_cmd = globals()['build_' + cmd]
        run_cmd()
    else:
        build_user()
        build_api()
        
if __name__ == '__main__':
    build()