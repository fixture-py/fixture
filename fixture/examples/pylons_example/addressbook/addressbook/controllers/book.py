import logging

from addressbook.lib.base import *
from addressbook.model import meta
from addressbook.model import Person

log = logging.getLogger(__name__)

class BookController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        c.persons = meta.Session.query(Person).join('my_addresses')
        return render("/book.mak")
