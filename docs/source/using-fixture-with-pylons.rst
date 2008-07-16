
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

First, `install Pylons`_ and create a new app as described in `Getting Started`_.  This will be an Address Book application so run the command as ``paster create -t pylons addressbook`` if you want to follow along with the code below.  Next, configure your models to use ``SQLAlchemy`` as explained in `Using SQLAlchemy with Pylons`_.  You should have added the module ``addressbook/models/meta.py``, defined ``init_model(engine)`` in ``addressbook/models/__init__.py``, added ``init_model(engine)`` to ``environment.py``, and configured ``BaseController`` to call ``meta.Session.remove()``.

Next configure routing and add a template, add controller, add template for book

Defining The Model
------------------

Adding Some Data Sets
---------------------

Defining A Fixture In The Test Suite
------------------------------------

Modify tests/__init__.py

Add setup code to tests/__init__.py

note about sharing the sqlite memory connection

warning about elixir

Writing A Test With Data
------------------------

Loading Initial Data
--------------------

setup-app


.. _install Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Installing+Pylons
.. _Getting Started: http://wiki.pylonshq.com/display/pylonsdocs/Getting+Started
.. _Using SQLAlchemy with Pylons: http://wiki.pylonshq.com/display/pylonsdocs/Using+SQLAlchemy+with+Pylons

