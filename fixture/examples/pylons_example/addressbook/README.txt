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

SQLAlchemy support added by following prompts on the command line of paster create.  Note that the requirement has been decremented to ==0.4.8 since fixture does not support 0.5+ yet.