
import os
from nose.exc import SkipTest
from fixture.test import conf

def setup():
    if not conf.POSTGRES_DSN:
        raise SkipTest

def compile_(code):
    """compiles code string for a module.
    
    returns dict w/ attributes of that module.
    """
    mod = {}
    eval(compile(code, 'stdout', 'exec'), mod)
    return mod