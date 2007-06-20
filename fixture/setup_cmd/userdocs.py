#!/usr/bin/env python

from distutils.cmd import Command
import os, sys, shutil
from os import path
import optparse
from fixture import docs
from fixture.test import teardown_examples
from docutils.core import (
    publish_file, publish_string, publish_doctree, publish_from_doctree)

class userdocs(Command):
    description = "create user documentation"
    user_options = [
        # ('optname=', None, ""),
    ]    
    # boolean_options = ['update']
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
        
    def run(self):
        """build end-user documentation."""
        
        # if options.build_dir:
        #     docs.builddir = options.build_dir
        if not path.exists(docs.builddir):
            os.mkdir(docs.builddir)
        docs.state_is_api = False
        docsdir = path.join(docs.builddir, 'docs')
        if not path.exists(docsdir):
            os.mkdir(docsdir)
    
        teardown_examples() # clear tmp files
        stylesheet = path.join(docs.srcdir, 'farmdev-docutils.css')
        body = publish_file(open(path.join(docs.srcdir, 'index.rst'), 'r'),
                    destination=open(path.join(docsdir, 'index.html'), 'w'),
                    writer_name='html',
                    settings_overrides={'stylesheet_path': stylesheet},
                    # settings_overrides={'halt_level':2,
                    #                     'report_level':5}
                    )
        f = open(path.join(docsdir, 'index.html'), 'w')
        f.write(body)
        f.close()
        shutil.copy(path.join(docs.srcdir, 'html4css1.css'), 
                    path.join(docsdir, 'html4css1.css'))
        shutil.copy(stylesheet, 
                    path.join(docsdir, 'farmdev-docutils.css'))
        images_target = path.join(docsdir, 'images')
        if path.exists(images_target):
            shutil.rmtree(images_target)
        shutil.copytree(path.join(docs.srcdir, 'images'), images_target)
        print "built user docs to %s" % docsdir

