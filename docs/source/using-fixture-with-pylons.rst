
.. _using-fixture-with-pylons:

-----------------------------------------------
Using Fixture To Test A Pylons + SQLAlchemy App
-----------------------------------------------

This explains how to use ``fixture`` in the test suite of a simple Address Book application written in `Pylons`_ powered by two tables in a `SQLite`_ database via `SQLAlchemy`_.  If you're not already familiar with :ref:`Using DataSet <using-dataset>` and :ref:`Using LoadableFixture <using-loadable-fixture>` then you'll be OK but it wouldn't hurt to read those docs first.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Pylons: http://pylonshq.com/
.. _SQLite: http://www.sqlite.org/

Creating An Address Book
------------------------

First, `install Pylons`_ and create a new app as described in `Getting Started`_.  This will be an Address Book application so run the command as ``paster create -t pylons addressbook`` if you want to follow along with the code below.  Next, configure your models to use ``SQLAlchemy`` as explained in `Using SQLAlchemy with Pylons`_.  You should have added the module ``addressbook/models/meta.py``, defined ``init_model(engine)`` in ``addressbook/models/__init__.py``, called ``init_model(engine)`` from ``environment.py``, and configured ``BaseController`` to call ``meta.Session.remove()``.

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

Per the `Pylons + SQLAlchemy documentation`_, you should have this line in your ``development.ini`` file which configures your model to use a local SQLite database in the file ``db.sqlite`` in the ``addressbook`` project dir::

	[app:main]
	# ...
	sqlalchemy.url = sqlite:///%(here)s/db.sqlite

Creating A Simple Controller
----------------------------
	
To show a simple list of addresses create a ``book`` controller::

	cd /path/to/addressbook
	paster controller book

This will create ``addressbook/controllers/book.py`` and addressbook/tests/functional/test_book.py``.  Then edit ``routing.py`` to make it the default page::

    # CUSTOM ROUTES HERE
    map.connect('', controller='book', action='index')

And edit ``addressbook/controllers/book.py`` to select some addressed from the database and render a template instead of returning "Hello World"::

    import logging

    from addressbook.lib.base import *
    from addressbook.model import meta
    from addressbook.model import Person

    log = logging.getLogger(__name__)

    class BookController(BaseController):

        def index(self):
            # c, defined in addressbook/lib/base.py, is automatically 
            # available in your template
            c.persons = meta.Session.query(Person).join('my_addresses')
            return render("/book.mak")

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

Fixture provides an easy way to add some data to your models for automated or exploratory testing.  Using a naming scheme where each :class:`DataSet <fixture.dataset.DataSet>` subclass is camel case named after a mapped classe in the model but ending in ``Data`` (more on :ref:`styles <using-loadable-fixture-style>`), define the following code in a new module at ``addressbook/datasets/__init__.py``::
	
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

See :ref:`Using DataSet <using-dataset>` for more info but in summary this sets up 1 row to be inserted into the ``people`` table and 2 rows to be inserted into the ``addresses`` table: two addresses for our man Joe Gibbs.

Loading Initial Data
--------------------

How do you fire up the dev server and see this data?  There is a way to do this by placing a few lines of code in ``addressbook/websetup.py`` to hook into the ``paster setup-app devlopment.ini`` command.

If you haven't already done so per the `Pylons + SQLAlchemy documentation`_ you will also need the initialization code here that creates the tables in your database.  The full code for creating tables and inserting the data defined above looks like this in ``addressbook/websetup.py``::

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
    
	    log.info("Creating tables")
	    meta.metadata.create_all(bind=meta.engine)
	    log.info("Successfully setup")
    
	    # load some initial data during setup-app
    
	    db = SQLAlchemyFixture(
	            env=model, style=NamedDataStyle(),
	            engine=meta.engine)
    
	    # quiet down fixture's own debug output 
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

Modify tests/__init__.py

Add setup code to tests/__init__.py

note about sharing the sqlite memory connection

warning about elixir

Writing A Test With Data
------------------------


setup-app


.. _install Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Installing+Pylons
.. _Getting Started: http://wiki.pylonshq.com/display/pylonsdocs/Getting+Started
.. _Pylons + SQLAlchemy documentation: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons
.. _Using SQLAlchemy with Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons

