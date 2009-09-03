import os
import sys
import logging
import fixture.examples.django_example

sys.path.append(os.path.dirname(fixture.examples.django_example.__file__))
## this is set by the test script?
# os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'


## handled by NoseDjango now?
# from django.core.management import call_command
# log = logging.getLogger('nose.django_loadable')
# 
# def setup():
#     call_command('syncdb', interactive=False)
#     call_command('reset', 'app', 'blog', interactive=False)