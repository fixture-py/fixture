import os
import sys

import django
from django.core.management import call_command

import fixture.examples


_EXAMPLE_PROJECT_DIR = os.path.dirname(fixture.examples.__file__)

_EXAMPLE_PROJECT_PATH = os.path.join(_EXAMPLE_PROJECT_DIR, 'django_example')

sys.path.append(_EXAMPLE_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_example.settings'
django.setup()

call_command('migrate', interactive=False, verbosity=0)
