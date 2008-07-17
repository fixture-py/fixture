
.. _using-temp-io:

-------------------------------
TempIO: A Temporary File System
-------------------------------

.. testsetup:: 

    import os

This object is useful for tests that need to set up a directory structure 
and work with files and paths.  Once you instantiate it, you have a temporary 
directory that will self-destruct when it falls out of scope:

.. doctest::

    >>> from fixture import TempIO
    >>> tmp = TempIO()
    >>> tmp #doctest: +ELLIPSIS
    '/.../tmp_fixture...'

Add sub-directories by simply assigning an attribute the basename of the new 
subdirectory, like so:

.. doctest::

    >>> tmp.incoming = "incoming"
    >>> os.path.exists(tmp.incoming)
    True

The new attribute is now an absolute path to a subdirectory, "incoming", of 
the tmp root, as well as an object itself.  Note that tmp and tmp.incoming are 
just string objects, but with several os.path methods mixed in for convenience.  
See the :class:`fixture.io.DeletableDirPath` API for details.  However, you can pass it to other objects and 
it will represent itself as its absolute path.

Putting Files
-------------

You can also insert files to the directory with putfile():

.. doctest::

    >>> foopath = tmp.incoming.putfile("foo.txt", "contents of foo")
    >>> tmp.incoming.join("foo.txt").exists()
    True

Removing The Temp Dir
---------------------

The directory root will self-destruct when it goes out of scope or ``atexit``. 
You can explicitly delete the object at your test's teardown if you like:

.. doctest::

    >>> tmpdir = str(tmp) # copy the directory path
    >>> del tmp
    >>> os.path.exists(tmpdir)
    False

API Documentation
-----------------

- :mod:`fixture.io`

.. _DirPath: ../apidocs/fixture.io.DirPath.html