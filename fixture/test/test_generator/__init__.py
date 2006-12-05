
import os

def setup():
    assert os.environ.has_key("FIXTURE_TEST_DSN_PG"), (
            "you need to define a postgres dsn in an environment var named "
            "FIXTURE_TEST_DSN_PG to run this test.  WARNING!  The DB user must "
            "be able to create tables and note that the tables will be deleted "
            "at teardown.")

def compile_(code):
    """compiles code string for a module.
    
    returns dict w/ attributes of that module.
    """
    mod = {}
    eval(compile(code, 'stdout', 'exec'), mod)
    return mod