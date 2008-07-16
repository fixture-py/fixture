
.. _using-fixture-with-pylons:

-----------------------------------------------
Using Fixture To Test A Pylons + SQLAlchemy App
-----------------------------------------------

This explains how to use ``fixture`` in the test suite of a simple Address Book application written in `Pylons`_ powered by two tables in a `SQLite`_ database via `SQLAlchemy`_.  If you're not already familiar with :ref:`Using DataSet <using-dataset>` and :ref:`Using LoadableFixture <using-loadable-fixture>` then you'll be OK but it wouldn't hurt to read those docs first.  The concepts here will probably also work with similar Python frameworks backed by `SQLAlchemy`_.  If you've got something working in another framework, please :ref:`let me know <index-contact>`.

Creating An Address Book
------------------------

First, `install Pylons`_ and create a new app as described in `Getting Started`_.  This will be an Address Book application so run the command as:: 

    paster create -t pylons addressbook

if you want to follow along with the code below.  Next, configure your models to use ``SQLAlchemy`` as explained in `Using SQLAlchemy with Pylons`_.  You should have added the module ``addressbook/models/meta.py``, defined ``init_model(engine)`` in ``addressbook/models/__init__.py``, called ``init_model(engine)`` from ``environment.py``, and configured ``BaseController`` to call ``meta.Session.remove()``.

Defining The Model
------------------

Next step is to define the data model.  Place the following code just below the ``init_model`` code you added before to ``addressbook/model/__init__.py`` to define the `SQLAlchemy`_ tables and mappers to hold the Address Book data.  The complete module should look like::

	import sqlalchemy as sa
	from sqlalchemy import orm

	from addressbook.model import meta

	def init_model(engine):
	    """Call me before using any of the tables or classes in the model."""

	    sm = orm.sessionmaker(autoflush=True, transactional=True, bind=engine)

	    meta.engine = engine
	    meta.Session = orm.scoped_session(sm)

	t_people = sa.Table('people', meta.metadata,
	    sa.Column('id', sa.types.Integer, primary_key=True),
	    sa.Column('name', sa.types.String(100)),
	    sa.Column('email', sa.types.String(100))
	)

	t_addresses_people = sa.Table('addresses_people', meta.metadata,
	    sa.Column('id', sa.types.Integer, primary_key=True),
	    sa.Column('person_id', sa.types.Integer, sa.ForeignKey('people.id')),
	    sa.Column('address_id', sa.types.Integer, sa.ForeignKey('addresses.id'))
	)

	t_addresses = sa.Table('addresses', meta.metadata,
	    sa.Column('id', sa.types.Integer, primary_key=True),
	    sa.Column('address', sa.types.String(100))
	)

	class Person(object):
	    pass

	class Address(object):
	    pass

	orm.mapper(Address, t_addresses)
	orm.mapper(Person, t_people, properties = {
	    'my_addresses' : orm.relation(Address, secondary = t_addresses_people),
	    })

Per the `Pylons + SQLAlchemy documentation`_, you should also have this line in your ``development.ini`` file which configures your model to use a local SQLite database in the file ``db.sqlite`` in the ``addressbook`` project dir::

	[app:main]
	# ...
	sqlalchemy.url = sqlite:///%(here)s/db.sqlite

Creating A Simple Controller
----------------------------
	
To show a simple list of addresses create a ``book`` controller::

	cd /path/to/addressbook
	paster controller book

This will create ``addressbook/controllers/book.py`` and ``addressbook/tests/functional/test_book.py``.  Edit ``routing.py`` to make it the default page::

    # CUSTOM ROUTES HERE
    map.connect('', controller='book', action='index')

(To avoid conflicts with the default page be sure to remove ``addressbook/public/index.html``.)

Edit ``addressbook/controllers/book.py`` to select some addressed from the database and render a template instead of returning "Hello World"::

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

(For more info see `passing variables to templates <http://wiki.pylonshq.com/display/pylonsdocs/Getting+Started#passing-variables-to-templates>`_.)

Add the template file as ``addressbook/templates/book.mak`` and write some Python code (via `Mako`_) to show some addresses::

	<h2>
	Address Book
	</h2>
	
	% for person in c.persons:
	    <h3>${person.name}</h3>
	    <h4>${person.email}</h4>
	    % for address in person.my_addresses:
	    <h4>${address.address}</h4>
	    % endfor
	% endfor

.. _Mako: http://www.makotemplates.org/

Adding Some Data Sets
---------------------

Now you have a page that lists addresses but you don't have any address data.  Fixture provides an easy way to add data to your models for automated or exploratory testing.  Define the following code in a new module at ``addressbook/datasets/__init__.py`` using a naming scheme where each :class:`DataSet <fixture.dataset.DataSet>` subclass is camel case, named after a mapped class in the model but ending in ``Data`` (:ref:`more on styles <using-loadable-fixture-style>`)::
	
	from fixture import DataSet

	class AddressData(DataSet):
	    class joe_in_kingston:
	        address = "111 Maple Ave, Kingston, Jamaica"
	    class joe_in_ny:
	        address = "111 S. 2nd Ave, New York, NY"

	class PersonData(DataSet):
	    class joe_gibbs:
	        name = "Joe Gibbs"
	        email = "joe@joegibbs.com"
	        my_addresses = [
	            AddressData.joe_in_kingston, 
	            AddressData.joe_in_ny]

This sets up one row to be inserted into the ``people`` table and two rows to be inserted into the ``addresses`` table -- the two addresses for our man Joe Gibbs.  See :ref:`Using DataSet <using-dataset>` for details.  Notice that the :ref:`Using DataSet <using-dataset>` classes mirror the properties we set up above in mappers.  This is because Fixture applies the DataSets to mapped classes ``Address`` and ``Person`` respectively to save the data.

Loading Initial Data
--------------------

How do you fire up the dev server and see this data?  There is a way to do this by placing a few lines of code in ``addressbook/websetup.py``, a Pylons convention to hook into the ``paster setup-app devlopment.ini`` command.

If you haven't already done so per the `Pylons + SQLAlchemy documentation`_ you will also need some code here to create the tables in your database.  The full code for creating tables and inserting data looks like this in ``addressbook/websetup.py``::

	"""Setup the addressbook application"""
	import logging

	from paste.deploy import appconfig
	from pylons import config

	from addressbook.config.environment import load_environment
	from addressbook import model
	from addressbook.model import meta

	from fixture import SQLAlchemyFixture
	from fixture.style import NamedDataStyle
	from addressbook.datasets import PersonData

	log = logging.getLogger(__name__)

	def setup_config(command, filename, section, vars):
	    """Place any commands to setup addressbook here"""
	    conf = appconfig('config:' + filename)
	    load_environment(conf.global_conf, conf.local_conf)
	    
	    # initialize the DB :
	    
	    log.info("Creating tables")
	    meta.metadata.create_all(bind=meta.engine)
	    log.info("Successfully setup")
	    
	    # load some initial data during setup-app :
	    
	    db = SQLAlchemyFixture(
	            env=model, style=NamedDataStyle(),
	            engine=meta.engine)
	            
	    # suppress fixture's own debug output 
	    # (activated by Paste) 
	    fl = logging.getLogger("fixture.loadable")
	    fl.setLevel(logging.CRITICAL)
	    fl = logging.getLogger("fixture.loadable.tree")
	    fl.setLevel(logging.CRITICAL)
	    
	    data = db.data(PersonData)
	    log.info("Inserting initial data")
	    data.setup()
	    log.info("Done")

This will allow you to get started on your Address Book application quickly by running::

	cd /path/to/addressbook
	paster setup-app development.ini

Thus, creating all tables in the ``db.sqlite`` file and loading the data defined above.  Now, start the development server::

	paster serve --reload development.ini

And load up `http://127.0.0.1:5000 <http://127.0.0.1:5000>`_ in your browser.  You should see a rendering of::

    <h2>
    Address Book
    </h2>

        <h3>Joe Gibbs</h3>
        <h4>joe@joegibbs.com</h4>
        <h4>111 Maple Ave, Kingston, Jamaica</h4>
        <h4>111 S. 2nd Ave, New York, NY</h4>

Defining A Fixture In The Test Suite
------------------------------------

Cool!  But what you really wanted was to write some automated tests, right?  Fixture makes that just as easy.  You can read more about `Unit Testing Pylons Apps <http://wiki.pylonshq.com/display/pylonsdocs/Unit+Testing>`_ but as of right now you should already have the file ``addressbook/tests/functional/test_book.py``, ready and waiting for some test code.  

Before running any tests you need to configure the test suite to make a database connection and create tables when the tests start.  First, edit ``test.ini`` to tell your app to use a SQLite memory connection so as not to disturb your development environment::
    
    [app:main]
    use = config:development.ini

    # Add additional test specific configuration options as necessary.
    sqlalchemy.url = sqlite:///:memory:

The `Pylons + SQLAlchemy documentation`_ suggests creating and dropping tables once per test but this doesn't scale very well and Fixture already tears down data automatically.  Instead, add ``setup`` and ``teardown`` methods to ``addressbook/tests/__init__.py``.  These methods will be called by nose_ *just once* per every run of your test suite.  Here is the code to add to ``addressbook/tests/__init__.py``::
    
    # other imports and setup ...
    
    from addressbook.model import meta
    
    def setup():
        meta.metadata.create_all(meta.engine)

    def teardown():
        meta.metadata.drop_all(meta.engine)
    
    # other test definitions ...

.. note:: Fixture deletes the rows *it* inserts.  If *your application* inserts rows of its own during a test then you will need to truncate the table or else use the strategy of creating / dropping tables once per test.

Similar to how the `Pylons + SQLAlchemy documentation`_ suggests, you still, however, need to remove the session once per test so that errors do not "leak" from test to test.  This is done by making the ``setUp`` method of ``TestController`` in ``__init__.py`` look like this::
        
    class TestController(TestCase):
        # ...
    
        def setUp(self):
            meta.Session.remove() # clear any stragglers from last test

To start using data in your tests, define a common fixture object to use throughout your test suite.  You also need to connect your database engine, so add this code to ``addressbook/tests/__init__.py``::

    # other imports and setup ...
        
    from addressbook import model
    from addressbook.model import meta
    from fixture import SQLAlchemyFixture
    from fixture.style import NamedDataStyle
        
    dbfixture = SQLAlchemyFixture(
        env=model,
        style=NamedDataStyle()
    )
    
    def setup():
        meta.metadata.create_all(meta.engine)
        # assign the engine here ...
        dbfixture.engine = meta.engine

    def teardown():
        meta.metadata.drop_all(meta.engine)
    
    # other test definitions ...

See :ref:`Using LoadableFixture <using-loadable-fixture>` for a detailed explanation of fixture objects.  Note here that the ``engine=`` keyword is left off of the :class:`SQLAlchemyFixture <fixture.loadable.sqlalchemy_loadable.SQLAlchemyFixture>` constructor.  That's just because SQLite memory databases are only available to a single *connection*.  Assigning ``dbfixture.engine`` during ``setup`` after table creation ensures that the right connection will be used.

Writing A Test With Data
------------------------

Open up the ``addressbook/tests/functional/test_book.py`` file and load up some data for the ``book`` controller to render.::
    
    from addressbook.model import meta, Person
    from addressbook.datasets import PersonData, AddressData
    from addressbook.tests import dbfixture
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
            assert AddressData.joe_in_kingston.address in response
            assert AddressData.joe_in_ny.address in response


A Note About Session Mappers and Elixir
---------------------------------------

warning about elixir

.. 

    UnloadError: InvalidRequestError: Instance 'Person@0x227d130' is with key (<class 'addressbook.model.Person'>, (1,), None) already persisted with a different identity (with <addressbook.model.Person object at 0x227d130> in <PersonData at 0x2272450 with keys ['joe_gibbs']>)

setup-app


.. _install Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Installing+Pylons
.. _Getting Started: http://wiki.pylonshq.com/display/pylonsdocs/Getting+Started
.. _Pylons + SQLAlchemy documentation: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons
.. _Using SQLAlchemy with Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Pylons: http://pylonshq.com/
.. _SQLite: http://www.sqlite.org/
.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

