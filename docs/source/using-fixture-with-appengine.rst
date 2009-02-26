
.. _using-fixture-with-appengine:

----------------------------------------------
Using Fixture To Test A Google App Engine Site
----------------------------------------------

This article looks at building and testing a simple Blog on `Google App Engine`_.  It shows how to use ``fixture`` to load objects into the `Datastore`_ and how to use 3rd party libraries to run tests in a sandboxed environment to mimic production.

The completed app can be found in the :ref:`fixture source code <download-fixture>` in ``fixture/examples/google_appengine_example/`` but portions of the source code are illustrated herein.  The example was written with `Google App Engine SDK`_ 1.1.1 and fixture 1.1.0 but may work with other versions.

For a more general overview of Google App Engine, the `Getting Started <http://code.google.com/appengine/docs/gettingstarted/>`_ section of the docs may help.

.. _Google App Engine: http://code.google.com/appengine/
.. _Google App Engine SDK: http://code.google.com/appengine/downloads.html
.. _Datastore: http://code.google.com/appengine/docs/datastore/
.. _WebTest: http://pythonpaste.org/webtest/

Creating a Simple Blog
----------------------

To run the example you'll first need to install the `Google App Engine SDK`_.  In the example directory you'll see there is a simple app.yaml file that looks like::
    
    application: pypi
    version: 1
    runtime: python
    api_version: 1

    handlers:
    - url: .*
      script: gblog/__init__.py

The app.yaml file is required for any Google App Engine site.  The module ``gblog/__init__.py`` defines the WSGI application, the point of entry into your site::
    
    application = webapp.WSGIApplication([
        (r'/', ListEntries),
            ], debug=True)

The handler ``ListEntries`` is defined in ``gblog/handlers.py`` and simply fetches entries and comments from the Datastore and sends them to the template ``list_entries.html`` for rendering.

The blog content is stored in two Datastore entities, ``Entry`` and ``Comment``, defined in ``gblog/models.py`` like this::

    from google.appengine.ext import db

    class Entry(db.Model):
        title = db.StringProperty()
        body = db.TextProperty()
        added_on = db.DateTimeProperty(auto_now_add=True)
    
    class Comment(db.Model):
        entry = db.ReferenceProperty(Entry)
        comment = db.TextProperty()
        added_on = db.DateTimeProperty(auto_now_add=True)

To run the example app as is, cd into ``fixture/examples/google_appengine_example/`` and type::

    $ dev_appserver.py .

Then open your browser to http://localhost:8080/ to view the app.
However, the result won't be very exciting because there aren't any blog entries yet.  In fact, you'll probably just see a blank page.  The next section should fix that.

Load Some Initial Data
----------------------

The ``fixture`` module lets you define :class:`DataSet <fixture.dataset.DataSet>` classes and load them into a local datastore for automated or exploratory testing.  Some sample data is defined in ``gblog/tests/datasets.py``::

    from fixture import DataSet

    class EntryData(DataSet):
        class great_monday:
            title = "Monday Was Great"
            body = """\
    Monday was the best day ever.  I got up (a little late, but that's OK) then I ground some coffee.  
    Mmmm ... coffee!  I love coffee.  Do you know about 
    <a href="http://www.metropoliscoffee.com/">Metropolis</a> coffee?  It's amazing.  Delicious.  
    I drank a beautiful cup of french pressed 
    <a href="http://www.metropoliscoffee.com/shop/coffee/blends.php">Spice Island</a>, had a shave 
    and went to work.  What a day!
    """

    class CommentData(DataSet):
        class monday_liked_it:
            entry = EntryData.great_monday
            comment = """\
    I'm so glad you have a blog because I want to know what you are doing everyday.  Heh, that sounds 
    creepy.  What I mean is it's so COOL that you had a great Monday.  I like Mondays too.
    """
        class monday_sucked:
            entry = EntryData.great_monday
            comment = """\
    Are you serious?  Mannnnnn, Monday really sucked.
    """

Using :class:`fixture.style.NamedDataStyle` these DataSet classes will map directly to the models defined above, ``Entry`` and ``Comment``, thus creating one new entry entitled "Monday Was Great" with two comments.

To load this up so you can see it in the dev site, you can run a script named ``load_data_locally.py`` which is part of the example code.  The script sets up the App Engine sandbox (code not shown) then loads data with an instance of :class:`GoogleDatastoreFixture <fixture.loadable.google_datastore_loadable.GoogleDatastoreFixture>`::
    
    from gblog import models
    from tests import datasets
    from fixture import GoogleDatastoreFixture
    from fixture.style import NamedDataStyle
    # ...
    
    datafixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())
    
    data = datafixture.data(datasets.CommentData, datasets.EntryData)
    data.setup()
    print "Data loaded into datastore"

Run the script with a path to a custom datastore::

    $ ./load_data_locally.py --datastore_path=./my.datastore

Then start the dev appserver pointing at your custom datastore::
    
    $ dev_appserver.py . --datastore_path=./my.datastore

Open http://localhost:8080/ in your browser and you should see a rendering of the "Monday Was Great" blog entry.

Testing A Google App Engine Site
--------------------------------

That's nice but you probably are more interested in loading sample data in a test suite.  To test an App Engine site I'm going to suggest first installing some 3rd party tools to make life easier:

- `WebTest`_
   
  - A module for testing WSGI compatible web apps
  - ``easy_install WebTest``

- `nose <http://www.somethingaboutorange.com/mrl/projects/nose/>`_
  
  - A pluggable command line script ``nosetests`` that discovers test files and executes them.
  - ``easy_install nose``

- `NoseGAE <http://code.google.com/p/nose-gae/>`_

  - This plugin adds options to nose to enable you to easily set up your GAE dev appserver environment for local testing.
  - ``easy_install NoseGAE`` 

After those are installed you should be able to cd into ``fixture/examples/google_datastore_loadable/`` and run all tests::

    $ nosetests --with-gae
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.852s

    OK

Here's what ``tests/test_list_entries.py`` looks like::
        
    import unittest
    from fixture import GoogleDatastoreFixture, DataSet
    from fixture.style import NamedDataStyle
    from gblog import application, models
    from webtest import TestApp
    from datasets import CommentData, EntryData

    datafixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())

    class TestListEntries(unittest.TestCase):
        def setUp(self):
            self.app = TestApp(application)
            self.data = datafixture.data(CommentData, EntryData)
            self.data.setup()
    
        def tearDown(self):
            self.data.teardown()
    
        def test_entries(self):
            response = self.app.get("/")
            print response
        
            assert EntryData.great_monday.title in response
            assert EntryData.great_monday.body in response
        
            assert CommentData.monday_liked_it.comment in response
            assert CommentData.monday_sucked.comment in response

A :class:`GoogleDatastoreFixture <fixture.loadable.google_datastore_loadable.GoogleDatastoreFixture>` is created with an ``env`` containing the Datastore Entities defined above (``gblog/models.py``).  The ``TestApp`` is the `WebTest`_ wrapper that allows you to call methods on your app object just like a browser would make requests.  It also facilities making assertions on the HTTP response returned by the app, among other things.  Here, the assert statements check that the data loaded during ``TestListEntries.setUp()`` was rendered in HTML.  By default nose hides stdout so the ``print response`` statement will only print to your shell if the test fails.

And there you have it.  Once again, you can download the :ref:`fixture source code <download-fixture>` and view this complete example app in ``fixture/examples/google_appengine_example/``.
