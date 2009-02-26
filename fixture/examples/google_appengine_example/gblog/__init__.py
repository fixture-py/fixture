
import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from gblog.handlers import *

log = logging.getLogger()

application = webapp.WSGIApplication([
    (r'/', ListEntries),
        ], debug=True)
         
def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()