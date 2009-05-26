
.. _using-fixture-with-pylons:

-----------------------------------------------
Using Fixture To Test A Pylons + SQLAlchemy App
-----------------------------------------------

This explains how to use ``fixture`` in the test suite of a simple Address Book application written in `Pylons`_ powered by two tables in a `SQLite`_ database via `SQLAlchemy`_.  If you're not already familiar with :ref:`Using DataSet <using-dataset>` and :ref:`Using LoadableFixture <using-loadable-fixture>` then you'll be OK but it wouldn't hurt to read those docs first.  The concepts here will probably also work with similar Python frameworks backed by `SQLAlchemy`_.  If you've got something working in another framework, please :ref:`let me know <index-contact>`.

(This tutorial was written with Python 2.5.2, fixture 1.3, Pylons 0.9.7, and SQLAlchemy 0.4.8 but may work with other versions.)

Creating An Address Book
------------------------

First, `install Pylons`_ and create a new app as described in `Getting Started`_.  This will be an Address Book application so run the command as:: 

    $ paster create -t pylons addressbook

Follow the prompts to use SQLAlchemy as the backend.

Defining The Model
------------------

To work with the database you need to define a data model.  Place the following code just below the ``init_model()`` to define the `SQLAlchemy`_ tables and mappers for the Address Book data.  The complete module should look like:

.. literalinclude:: ../../fixture/examples/pylons_example/addressbook/addressbook/model/__init__.py
    :language: python

Take note that by default Pylons sets your sqlalchemy database to sqlite::

    [app:main]
    # ...
    sqlalchemy.url = sqlite:///%(here)s/development.db

.. note::
    
    For reference, all code shown here is available from the `fixture code repository <http://code.google.com/p/fixture/source/browse>`_ in ``fixture/examples/pylons_example/addressbook``.

Creating A Simple Controller
----------------------------
    
Create a ``book`` controller to show a simple list of addresses::

    $ cd /path/to/addressbook
    $ paster controller book

This makes the files ``addressbook/controllers/book.py`` and ``addressbook/tests/functional/test_book.py``.  Edit ``routing.py`` to set it as the default page::

    # CUSTOM ROUTES HERE
    map.connect('/', controller='book', action='index')

(To avoid conflicts with the default page also be sure to remove ``addressbook/public/index.html``.)

Edit ``addressbook/controllers/book.py`` to select some addresses from the database and render a template instead of returning "Hello World":

.. literalinclude:: ../../fixture/examples/pylons_example/addressbook/addressbook/controllers/book.py
    :language: python

Add the template file as ``addressbook/templates/book.mako`` and write some Python code (via `Mako`_) to show some addresses:

.. literalinclude:: ../../fixture/examples/pylons_example/addressbook/addressbook/templates/book.mako
    :language: html

.. _Mako: http://www.makotemplates.org/

Adding Some Data Sets
---------------------

You now have a page that lists addresses but you don't have any address data.  Fixture provides an easy way to add data to your models for automated or exploratory testing.  Define the following code in a new module at ``addressbook/datasets/__init__.py`` using a naming scheme where each :class:`DataSet <fixture.dataset.DataSet>` subclass is camel case, named after a mapped class in the model but ending in ``Data`` (:ref:`read more about styles here <using-loadable-fixture-style>`):

.. literalinclude:: ../../fixture/examples/pylons_example/addressbook/addressbook/datasets/__init__.py
    :language: python

This sets up one row to be inserted into the ``people`` table and two rows to be inserted into the ``addresses`` / ``addresses_people`` tables, declaring two addresses for our man Joe Gibbs.  See :ref:`Using DataSet <using-dataset>` for the details about these classes.  

Notice that the :class:`DataSet <fixture.dataset.DataSet>` classes mirror the properties we defined above for the mappers.  This is because Fixture applies the DataSets to the mapped classes ``Address`` and ``Person`` respectively to save the data.

Loading Initial Data
--------------------

If you want to fire up the dev server and start using this data, you just need to place a few lines of code in ``addressbook/websetup.py``, a Pylons convention for hooking into the ``paster setup-app devlopment.ini`` command.

The full code for creating tables and inserting data looks like this in ``addressbook/websetup.py``:

.. literalinclude:: ../../fixture/examples/pylons_example/addressbook/addressbook/websetup.py
    :language: python

This will allow you to get started on your Address Book application by running::

    $ cd /path/to/addressbook
    $ paster setup-app development.ini

Now, start the development server::

    paster serve --reload development.ini

And load up `http://127.0.0.1:5000 <http://127.0.0.1:5000>`_ in your browser.  You should see a rendering of::

    <h2>
    Address Book
    </h2>

        <h3>Joe Gibbs</h3>
        <h4>joe@joegibbs.com</h4>
        <h4>111 St. James St, Montego Bay, Jamaica</h4>
        <h4>111 S. 2nd Ave, New York, NY</h4>

Cool!  But what you really wanted was to write some automated tests, right?  Fixture makes that just as easy.  You can read more about `Unit Testing Pylons Apps <http://wiki.pylonshq.com/display/pylonsdocs/Unit+Testing>`_ but as of right now you should already have the file ``addressbook/tests/functional/test_book.py``, ready and waiting for some test code.  

Setting Up The Test Suite
-------------------------

Before running any tests you need to configure the test suite to make a database connection and create tables when the tests start.  First, edit ``test.ini`` to tell your app to use a different database file so as not to disturb your development environment::
    
    [app:main]
    use = config:development.ini

    # Add additional test specific configuration options as necessary.
    sqlalchemy.url = sqlite:///%(here)s/tests.db


.. note::

    By default Pylons configures your test suite so that the same code run by ``paster setup-app test.ini`` is run before your tests start.  This can be confusing if you are creating tables and inserting data as mentioned in the previous section so replace it with this code in ``addressbook/tests/__init__.py`` :

::

    # additional imports ...
    from paste.deploy import appconfig
    from addressbook.config.environment import load_environment
    
    # Invoke websetup with the current config file
    ##### comment this out so that initial data isn't loaded:
    # SetupCommand('setup-app').run([config['__file__']])

    ##### but add this so that your models get configured:
    appconf = appconfig('config:' + config['__file__'])
    load_environment(appconf.global_conf, appconf.local_conf)
    
    # ...

Also, the `Pylons + SQLAlchemy documentation`_ suggests creating and dropping tables once per test but this doesn't scale very well and Fixture already tears down data automatically.  Instead, add ``setup`` and ``teardown`` methods to ``addressbook/tests/__init__.py``.  These methods will be called by nose_ just once per every run of your test suite.  Here is the code to add to ``addressbook/tests/__init__.py``::
    
    # additional imports ...
    from addressbook.model import meta
    
    # add this code ...
    
    def setup():
        meta.metadata.create_all(meta.engine)

    def teardown():
        meta.metadata.drop_all(meta.engine)
    
    # ...

.. note:: Fixture deletes the rows *it* inserts.  If *your application* inserts rows during a test then you will need to truncate the table or else go back to the strategy of creating / dropping tables per every test.

Similar to how the `Pylons + SQLAlchemy documentation`_ suggests, you still, however, need to remove the session once *per test* so that objects do not "leak" from test to test.  This is done by making the ``setUp`` method of ``TestController`` in ``tests/__init__.py`` look like this::

    class TestController(TestCase):
        # ...
    
        def setUp(self):
            meta.Session.remove() # clear any stragglers from last test

Defining A Fixture
------------------

To start using data in your tests, first define a common fixture object to use throughout your test suite by adding this code to ``addressbook/tests/__init__.py``::
    
    # be sure to export dbfixture :
    __all__ = ['url_for', 'TestController', 'dbfixture']
    
    # add this code *AFTER* load_environment(...) :

    # additional imports ...
    from addressbook import model
    from addressbook.model import meta
    from fixture import SQLAlchemyFixture
    from fixture.style import NamedDataStyle
    
    dbfixture = SQLAlchemyFixture(
        env=model,
        engine=meta.engine,
        style=NamedDataStyle()
    )
    
    # ...

.. note:: Beware that using an in-memory SQLite database would make this trickier and the above strategy won't work.  Instead you'd need to assign the engine in ``setup`` after ``metadata.create_all()`` since SQLite memory databases are only available to a single *connection*.

See :ref:`Using LoadableFixture <using-loadable-fixture>` for a detailed explanation of fixture objects.  

Testing With Data
-----------------

Now let's start working with the :class:`DataSet <fixture.dataset.DataSet>` objects.  Edit ``addressbook/tests/functional/test_book.py`` so that it looks like this::
    
    from addressbook.model import meta, Person
    from addressbook.datasets import PersonData, AddressData
    from addressbook.tests import *

    class TestBookController(TestController):

        def setUp(self):
            super(TestBookController, self).setUp()
            self.data = dbfixture.data(PersonData) # AddressData loads implicitly
            self.data.setup()
    
        def tearDown(self):
            self.data.teardown()
            super(TestBookController, self).tearDown()
        
        def test_index(self):
            response = self.app.get(url_for(controller='book'))
            print response
            assert PersonData.joe_gibbs.name in response
            assert PersonData.joe_gibbs.email in response
            assert AddressData.joe_in_montego.address in response
            assert AddressData.joe_in_ny.address in response

Then run the test, which should pass::

    $ cd /path/to/addressbook
    $ nosetests
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.702s

    OK

Woo!

This code is asserting that the values from the :class:`DataSet <fixture.dataset.DataSet>` classes have been rendered on the page, i.e. ``<h4>joe@joegibbs.com</h4>``.  There is more info on using response objects in the `WebTest`_ docs (however at the time of this writing Pylons is still using ``paste.fixture``, an earlier form of ``WebTest``).  

You'll notice there is a print statement showing the actual response.  By default nose hides stdout for convenience so if you want to see the response just trigger a failure by adding ``raise AssertionError`` in the test.

::
    
    $ nosetests
    F
    ======================================================================
    FAIL: test_index (addressbook.tests.functional.test_book.TestBookController)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/Users/kumar/.../addressbook/tests/functional/test_book.py", line 16, in test_index
        raise AssertionError
    AssertionError: 
    -------------------- >> begin captured stdout << ---------------------
    Response: 200
    content-type: text/html; charset=utf-8
    pragma: no-cache
    cache-control: no-cache
    <h2>
    Address Book
    </h2>
        <h3>Joe Gibbs</h3>
        <h4>joe@joegibbs.com</h4>
        <h4>111 St. James St, Montego Bay, Jamaica</h4>
        <h4>111 S. 2nd Ave, New York, NY</h4>

    --------------------- >> end captured stdout << ----------------------

    ----------------------------------------------------------------------
    Ran 1 test in 0.389s

    FAILED (failures=1)

A Note About Session Mappers and Elixir
---------------------------------------

If you are using `Session.mapper(TheClass, the_table) <http://www.sqlalchemy.org/docs/04/session.html#unitofwork_contextual_associating>`_ instead of just plain ol' ``mapper(...)`` then you are introducing a potential problem in that your objects will save themselves to the wrong session.  You'll need to fix it by setting ``save_on_init=False`` like this::

    meta.Session.mapper(Address, t_addresses, save_on_init=False)
    meta.Session.mapper(Person, t_people, properties = {...}, save_on_init=False)

For convenience, this is the **default** behavior in `Elixir`_.  If working with `Elixir Entities <http://elixir.ematia.de/trac/wiki/TutorialDivingIn#a2.Averysimplemodel>`_ then construct your entities like this::

    class Person(Entity):
        name = Field(String(100))
        email = Field(String(100))
        has_many('addresses', of_kind='Address')
        # :
        using_mapper_options(save_on_init=False)

The side effect is that your app will always have to call ``person.save_or_update()`` whenever it wants to write data.

Why Do I Keep Getting InvalidRequestError?
------------------------------------------

If you've seen an error during unload like::
    
    UnloadError: InvalidRequestError: Instance 'Person@0x227d130' with key 
    (<class 'addressbook.model.Person'>, (1,), None) is already persisted with a different identity 
    (with <addressbook.model.Person object at 0x227d130> in 
    <PersonData at 0x2272450 with keys ['joe_gibbs']>)

then it probably means you have either called ``data.setup()`` twice without calling ``data.teardown()`` in between or else you somehow saved the same ``Person()`` object to two different sessions.  If using an in-memory database be sure you have commented out the code that runs ``setup-app`` in ``tests/__init__.py`` (see above).  You also might see this if you forget to set ``save_on_init=False`` to your mapped classes (also see above).

Example Source
--------------

That's it!  Have fun.

This code is available from the `fixture code repository <http://code.google.com/p/fixture/source/browse>`_ in ``fixture/examples/pylons_example/addressbook``.

.. _install Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Installing+Pylons
.. _Getting Started: http://wiki.pylonshq.com/display/pylonsdocs/Getting+Started
.. _Pylons + SQLAlchemy documentation: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons
.. _Using SQLAlchemy with Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Elixir: http://elixir.ematia.de/
.. _Pylons: http://pylonshq.com/
.. _SQLite: http://www.sqlite.org/
.. _nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _WebTest: http://pythonpaste.org/webtest/
