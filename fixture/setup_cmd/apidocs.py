from distutils.cmd import Command
import os, sys, shutil
from os import path
import optparse
from fixture import docs
from fixture.test import teardown_examples
from docutils.core import (
    publish_file, publish_string, publish_doctree, publish_from_doctree)
    

class apidocs(Command):
    description = "create API documentation"
    user_options = [
        # ('optname=', None, ""),
    ]    
    # boolean_options = ['update']
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
        
    def run(self):
        """build API documentation."""
    
        # if options.build_dir:
        #     docs.builddir = options.build_dir
        if not path.exists(docs.builddir):
            os.mkdir(docs.builddir)
        docs.state_is_api = True
        from pydoctor.driver import main
        argv = [
            '--html-output=%s/apidocs' % docs.builddir, '--project-name=fixture', 
            '--docformat=restructuredtext',
            '--project-url=http://code.google.com/p/fixture/', '--make-html', 
            '--add-package=fixture', '--verbose', '--verbose']
    
        sys.argv[0] = ['pydoctor'] # can't remember why
        main(argv)