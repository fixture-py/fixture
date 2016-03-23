#!/usr/bin/env python
import os
import sys

import fixture.examples

_EXAMPLE_PROJECT_DIR = os.path.dirname(fixture.examples.__file__)

_EXAMPLE_PROJECT_PATH = os.path.join(_EXAMPLE_PROJECT_DIR, 'django_example')

sys.path.append(_EXAMPLE_PROJECT_PATH)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_example.settings")

    from django.core.management import execute_from_command_line, call_command
    import django
    django.setup()
    call_command('migrate', interactive=False, verbosity=0)

    execute_from_command_line(sys.argv)
