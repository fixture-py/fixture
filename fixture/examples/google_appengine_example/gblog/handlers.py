
import os
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from gblog.models import *

log = logging.getLogger()

def tpl_path(template_file_name):
    return os.path.join(os.path.dirname(__file__), 'templates', template_file_name)

class ListEntries(webapp.RequestHandler):
    def get(self):
        entries = Entry.all()
        entries_comments = [(e, [c for c in Comment.all().filter("entry =", e)]) for e in entries]
        log.info(entries_comments)
        tpl = {
            'entries_comments': entries_comments,
        }
        self.response.out.write(template.render(tpl_path('list_entries.html'), tpl))