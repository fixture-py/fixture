import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'


from django.core.management import call_command
log = logging.getLogger('nose.django_loadable')

def setup():
    call_command('syncdb')
    call_command('reset', 'app', 'blog')