.. _using-fixture-command:

-------------------------
Using the fixture command
-------------------------

.. contents:: :local:

There are several issues you may run into while working with fixtures:  

1. The data model of a program is usually an implementation detail.  It's bad practice to "know" about implementation details in tests because it means you have to update your tests when those details change; you should only have to update your tests when an interface changes.  
2. Data accumulates very fast and there is already a useful tool for slicing and dicing data: the database!  Hand-coding DataSet classes is not always the way to go.
3. When regression testing or when trying to reproduce a bug, you may want to grab a "snapshot" of the existing data.

``fixture`` is a shell command to address these and other issues.  It gets installed along with this module.  Specifically, the ``fixture`` command accepts a path to a single object and queries that object using the command options.  The output is python code that you can use in a test to reload the data retrieved by the query.  

An Example With SQLAlchemy 
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testsetup:: command
    
    import os
    if os.path.exists('/tmp/fixture_example.db'):
        os.unlink('/tmp/fixture_example.db')

Here is a data model defined in `SQLAlchemy <http://www.sqlalchemy.org/>`_ code:

.. doctest:: command

    >>> from sqlalchemy import *
    >>> from sqlalchemy.orm import *
    >>> metadata = MetaData()
    >>> authors = Table('authors', metadata,
    ...     Column('id', Integer, primary_key=True),
    ...     Column('first_name', String(100)),
    ...     Column('last_name', String(100)))
    ... 
    >>> class Author(object):
    ...     pass
    ...     
    >>> books = Table('books', metadata, 
    ...     Column('id', Integer, primary_key=True),
    ...     Column('title', String(100)),
    ...     Column('author_id', Integer, ForeignKey('authors.id')))
    ...     
    >>> class Book(object):
    ...     pass
    ...     
    >>> m = mapper(Author, authors) # doctest:+ELLIPSIS
    >>> m = mapper(Book, books, properties={
    ...     'author': relation(Author)
    ... })
    >>> 

After inserting some data, it would be possible to run a command that points at the ``Book`` object, sends it a SQL query with a custom where clause, and turns the record sets into ``DataSet`` classes:

.. shell:: fixture --dsn=sqlite:////tmp/fixture_example.db --where="title='Dune'" fixture.examples.db.sqlalchemy_examples.Book
   :run_on_method: fixture.command.generate.main
   :setup:         fixture.docs.setup_command_data

Notice that we only queried the ``books`` table but we got back all the necessary foreign keys that were needed to reproduce the data (in this case, the ``authors`` data).

Usage
~~~~~

.. shell:: fixture --help
   :run_on_method: fixture.command.generate.main
   
Creating a custom data handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No documentation yet
