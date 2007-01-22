
import sys, os
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

## in setup.cfg for nosetests
# os.environ['NOSE_WITH_COVERAGE'] = "1"
# os.environ['NOSE_WITH_DOCTEST'] = "1"
# os.environ['NOSE_COVER_PACKAGES'] = "fixture"
# os.environ['NOSE_VERBOSE'] = "1"

class Package(object):
    """encapsulates the package to setup."""            
    _real_module = None
    def _get_module(self):
        if self._real_module is None:
            import fixture
            self._real_module = fixture
        return self._real_module
    module = property(_get_module)
    
    docparts = None
    def _get_from_doc(self, index):
        if self.docparts is None:
            import inspect
            from pydoc import splitdoc
            self.docparts = splitdoc(inspect.getdoc(self.module))
        return self.docparts[index]
    
    description = property(fget=lambda s: s._get_from_doc(0))
    long_description = property(fget=lambda s: s._get_from_doc(1))
    version = property(fget=lambda s: getattr(s.module, '__version__'))
package = Package()

setup(
    name = 'fixture',
    version = package.version,
    author = 'Kumar McMillan',
    author_email = 'kumar dot mcmillan / gmail.com',
    description = package.description,
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
    long_description = package.long_description,
    license = 'GNU Lesser General Public License (LGPL)',
    keywords = ('test testing tools unittest fixtures setup teardown '
                'database stubs IO tempfile'),
    url = 'http://farmdev.com/',
    download_url = 'http://farmdev.com/src/fixture-%s-py%s.%s.egg' % \
                    (   package.version, sys.version_info[0], 
                        sys.version_info[1]),
    packages = find_packages(),
    
    install_requires=('nose>=0.9.2',),
    # test_suite="nose.collector",
    entry_points = { 
        'console_scripts': [ 'fixture = fixture.command.generate:main' ] 
        },
    extras_require = {
        'sqlobject': ['SQLObject>=0.7'],
        'sqlalchemy': ['sqlalchemy>=0.3'],
        'lxml': ['lxml'],
        },
    )