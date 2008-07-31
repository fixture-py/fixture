
import logging
from google.appengine.ext import db

log = logging.getLogger()

class Entry(db.Model):
    title = db.StringProperty()
    body = db.TextProperty()
    added_on = db.DateTimeProperty(auto_now_add=True)
    
class Comment(db.Model):
    entry = db.ReferenceProperty(Entry)
    comment = db.TextProperty()
    added_on = db.DateTimeProperty(auto_now_add=True)

    