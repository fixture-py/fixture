
from fixture import TempIO
import os

LITE_DSN = os.environ.get('FIXTURE_TEST_LITE_DSN', 'sqlite:///:memory:')
HEAVY_DSN = os.environ.get('FIXTURE_TEST_HEAVY_DSN', None)
HEAVY_DSN_IS_TEMPIO = False

def reset_heavy_dsn():
    global HEAVY_DSN
    if HEAVY_DSN_IS_TEMPIO:        
        tmp = TempIO(deferred=True)
        HEAVY_DSN = 'sqlite:///%s' % tmp.join("tmp.db")