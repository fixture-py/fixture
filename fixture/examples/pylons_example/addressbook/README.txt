This file is for you to describe the addressbook application. Typically
you would include information such as the information below:

Installation and Setup
======================

Install ``addressbook`` using easy_install::

    easy_install addressbook

Make a config file as follows::

    paster make-config addressbook config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Then you are ready to go.

About This Example App
======================

SQLAlchemy support added per http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons
