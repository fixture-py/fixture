import logging

from addressbook.lib.base import *
from addressbook.model import meta, Person

log = logging.getLogger(__name__)

class BookController(BaseController):

    def index(self):
        # c, imported from addressbook/lib/base.py, is automatically 
        # available in your template
        c.persons = meta.Session.query(Person).join('my_addresses')
        return render("/book.mak")
