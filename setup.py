
import sys
import ez_setup
ez_setup.use_setuptools()
import inspect
from pydoc import splitdoc

from setuptools import setup, find_packages
import fixture

description, long_description = splitdoc(inspect.getdoc(fixture))

setup(
    name = 'fixture',
    version = fixture.__version__,
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
    url = 'http://farmdev.com/',
    download_url = 'http://farmdev.com/src/fixture-%s-py%s.%s.egg' % \
                    (   fixture.__version__, sys.version_info[0], 
                        sys.version_info[1]),
    packages = find_packages(),
    entry_points = { 'console_scripts': [ 
                        'fixture = fixture.command.generate:main' ] },
    )