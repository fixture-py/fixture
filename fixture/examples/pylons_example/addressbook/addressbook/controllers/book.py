import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from addressbook.lib.base import BaseController, render
from addressbook.model import meta, Person

log = logging.getLogger(__name__)

class BookController(BaseController):

    def index(self):
        # c, imported from addressbook/lib/base.py, is automatically 
        # available in your template
        c.persons = meta.Session.query(Person).join('my_addresses')
        return render("/book.mako")
