import os

from setuptools import setup, find_packages


_CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
_VERSION = \
    open(os.path.join(_CURRENT_DIR_PATH, 'VERSION.txt')).readline().rstrip()

_LONG_DESCRIPTION = """
It provides several utilities for achieving a *fixed state* when testing
Python programs.  Specifically, these utilities setup / teardown databases and
work with temporary file systems.

You may want to start by reading the `End User Documentation`_.

.. _End User Documentation: http://farmdev.com/projects/fixture/docs/
"""


setup(
    name='fixture',
    version=_VERSION,
    author='Kumar McMillan',
    author_email='kumar dot mcmillan / gmail.com',
    description='fixture is a package for loading and referencing test data',
    classifiers=['Environment :: Other Environment',
                 'Intended Audience :: Developers',
                 ('License :: OSI Approved :: GNU Library or Lesser '
                  'General Public License (LGPL)'),
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing',
                 'Topic :: Software Development :: Quality Assurance',
                 'Topic :: Utilities'],
    long_description=_LONG_DESCRIPTION,
    license='GNU Lesser General Public License (LGPL)',
    keywords=('test testing tools unittest fixtures setup teardown '
              'database stubs IO tempfile'),
    url='http://farmdev.com/projects/fixture/',

    packages=find_packages(),

    test_suite="fixture.setup_test_not_supported",
    entry_points={
        'console_scripts': ['fixture = fixture.command.generate:main']
    },
    install_requires=[
        'six >= 1.10.0',
    ],
    # the following allows e.g. easy_install fixture[django]
    extras_require={
        'decorators': ['nose>=0.9.2'],
        'sqlalchemy': ['SQLAlchemy>=0.4'],
        'sqlobject': ['SQLObject==0.8'],
        'django': ['django>=1.8'],
    },
)
