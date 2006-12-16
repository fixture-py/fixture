
import os

MEM_DSN = 'sqlite:///:memory:'
POSTGRES_DSN = os.environ.get('FIXTURE_TEST_POSTGRES_DSN', None)