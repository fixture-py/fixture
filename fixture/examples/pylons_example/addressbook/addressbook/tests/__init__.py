"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.
"""
from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
from pylons import config, url
from routes.util import URLGenerator
from webtest import TestApp

import pylons.test

__all__ = ['environ', 'url', 'TestController', 'dbfixture']

# Invoke websetup with the current config file
SetupCommand('setup-app').run([config['__file__']])

environ = {}

from addressbook import model
from addressbook.model import meta
from fixture import SQLAlchemyFixture
from fixture.style import NamedDataStyle

dbfixture = SQLAlchemyFixture(
    env=model,
    engine=meta.engine,
    style=NamedDataStyle()
)

def setup():
    meta.metadata.create_all(meta.engine)

def teardown():
    meta.metadata.drop_all(meta.engine)

class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestCase.__init__(self, *args, **kwargs)
        
    # def setUp(self):
    #     meta.Session.remove() # clear any stragglers from last test
