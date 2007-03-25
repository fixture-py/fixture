
import os

LITE_DSN = os.environ.get('FIXTURE_TEST_LITE_DSN', 'sqlite:///:memory:')
HEAVY_DSN = os.environ.get('FIXTURE_TEST_HEAVY_DSN', None)