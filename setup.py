
import sys, os
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
import compiler
import pydoc
from compiler import visitor

class ModuleVisitor(object):
    def __init__(self):
        self.mod_doc = None
        self.mod_version = None
        
    def default(self, node):
        for child in node.getChildNodes():
            self.visit(child)
            
    def visitModule(self, node):
        self.mod_doc = node.doc
        self.default(node)
        
    def visitAssign(self, node):
        if self.mod_version:
            return
        asn = node.nodes[0]
        assert asn.name == '__version__', (
            "expected __version__ node: %s" % asn)
        self.mod_version = node.expr.value
        self.default(node)
        
def get_module_meta(modfile):            
    ast = compiler.parseFile(modfile)
    modnode = ModuleVisitor()
    visitor.walk(ast, modnode)
    if modnode.mod_doc is None:
        raise RuntimeError(
            "could not parse doc string from %s" % modfile)
    if modnode.mod_version is None:
        raise RuntimeError(
            "could not parse __version__ from %s" % modfile)
    return (modnode.mod_version,) + pydoc.splitdoc(modnode.mod_doc)

version, description, long_description = get_module_meta("./fixture/__init__.py")

setup(
    name = 'fixture',
    version = version,
    author = 'Kumar McMillan',
    author_email = 'kumar dot mcmillan / gmail.com',
    description = description,
    classifiers = [ 'Environment :: Other Environment',
                    'Intended Audience :: Developers',
                    (   'License :: OSI Approved :: GNU Library or Lesser '
                        'General Public License (LGPL)'),
                    'Natural Language :: English',
                    'Operating System :: OS Independent',
                    'Programming Language :: Python',
                    'Topic :: Software Development :: Testing',
                    'Topic :: Software Development :: Quality Assurance',
                    'Topic :: Utilities'],
    long_description = long_description,
    license = 'GNU Lesser General Public License (LGPL)',
    keywords = ('test testing tools unittest fixtures setup teardown '
                'database stubs IO tempfile'),
    url = 'http://farmdev.com/projects/fixture/',
    
    packages = find_packages(),
    
    test_suite="fixture.setup_test_not_supported",
    entry_points = { 
        'console_scripts': [ 'fixture = fixture.command.generate:main' ] 
        },
    tests_require=[
        'testtools', 'psycopg2', 'SQLObject>=0.8', 'Elixir>=0.5', 
        'nose>=0.10.3', 'SQLAlchemy>=0.4,<0.5', 'Sphinx>=0.4'],
    extras_require = {
        'decorators': ['nose>=0.9.2'],
        'sqlalchemy': ['SQLAlchemy>=0.4'],
        'sqlobject': ['SQLObject>=0.8'],
        },
    )