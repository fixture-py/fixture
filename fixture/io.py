
"""Working with temporary file systems.

.. contents::

TempIO: a self-destructing, temporary file system
-------------------------------------------------

This object is useful for tests that need to set up a directory structure 
and work with its files and paths.  You can create a directory simply by setting 
an attribute to the new directory's path::

    >>> from fixture import TempIO
    >>> tmp = TempIO()
    >>> tmp.incoming = "incoming"
    >>> tmp.incoming.exists()
    True

The value "incoming" created a subdirectory named incoming of the tmp root 
and stored a new DirPath object in the object.

The new attribute is now an absolute path to a subdirectory, "incoming", of 
the tmp root.  Note that tmp and tmp.incoming are string objects but with 
several os.path methods mixed in for convenience.  However, you can pass it 
to other objects and it will represent itself as its absolute path.

You can also insert files to the directory with putfile()::

    >>> foopath = tmp.incoming.putfile("foo.txt", "contents of foo")
    >>> tmp.incoming.join("foo.txt").exists()
    True

The directory root will self-destruct when it goes out of scope or atexit. 
You can explicitly delete the object at your test's teardown if you like::

    >>> tmpdir = str(tmp) # making sure it's a copy
    >>> del tmp
    >>> os.path.exists(tmpdir)
    False

"""
__all__ = ['TempIO']

import os, sys
from os import path
from os.path import join, exists, split, basename
from tempfile import mkdtemp
import atexit
_tmpdirs = set()

def TempIO(deferred=False, **kw):
    """self-destructing, temporary directory.
    
    Takes the same keyword args as tempfile.mkdtemp with these additional 
    keywords:
    
    - deferred
    
        - if True, destruction will be put off until atexit.  Otherwise, 
          it will be destructed when it falls out of scope
              
    """
    if not 'prefix' in kw:
        # a breadcrumb ...
        kw['prefix'] = 'tmp_fixture_'
    
    tmp_path = path.realpath(mkdtemp(**kw))
    root = DeletableDirPath(tmp_path)
    root._deferred = deferred
    _tmpdirs.add(tmp_path)
    return root

def _expunge(tmpdir):
    """called internally to remove a tmp dir."""
    if exists(tmpdir):
        import shutil
        shutil.rmtree(tmpdir)
        
def _expunge_all():
    """exit function to remove all registered tmp dirs."""
    for d in _tmpdirs:
        _expunge(d)
    
# this seems to be a safer way to clean up since __del__ can
# be called in an unpredictable environment :
atexit.register(_expunge_all)

def mkdirall(path, mkdir=os.mkdir):
    """walks the path and makes any non-existant dirs.
    
    optional keyword `mkdir` is the callback for making a single dir
    
    """
    if path[-1] == os.path.sep: 
        path = path[0:-len(os.path.sep)] # trailing slash confused exists()
        
    root = (path[0] == os.path.sep) and os.path.sep or ''
    paths = split(path)[0].split(os.path.sep)
    if len(paths):
        accum = ''
        for p in paths:
            if p is '':
                continue # slash prefix will cause this
            accum = join(accum, p)
            abs = join(root, accum)
            if not exists(abs): mkdir(abs)
    
    mkdir(path)

def putfile(filename, contents, filelike=None, mode=None):
    """opens filename in writing mode, writes contents and closes.
    
    if filelike is None then it will be created with open() and the
    prefixed path will be walked to create non-existant dirs.
    
    """
    if mode is None:
        mode = 'w'
    if filelike is None:
        parent = split(filename)[0]
        if parent and not exists(parent):
            mkdirall(parent)
        filelike = open(filename, mode)
        
    filelike.write(contents)
    filelike.close()
    
class DirPath(str, object):
    """a directory path.
    
    The instance will function exactly like a string but is enhanced with a few 
    common methods from os.path.  Note that path.split() is implemented as 
    self.splitpath() since otherwise paths may not work right in other 
    applications.
    
    """
    def __init__(self, path):
        str.__init__(self, path)
        
    def __setattr__(self, name, val):
        """self.new_directory = "rel/path/to/directory" 
        
        a new attribute will be created as a relative directory and the value 
        will be stored as a new DirPath object.
        
        """
        if not name.startswith('_'):
            path = self.mkdir(val)
            val = self._wrap(path)
        object.__setattr__(self, name, val)
    
    def _wrap(self, path):
        return DirPath(path)
        
    def abspath(self):
        """os.path.abspath(self)"""
        return self._wrap(path.abspath(self))
    
    def basename(self):
        """os.path.basename(self)"""
        return self._wrap(path.basename(self))
    
    def dirname(self):
        """os.path.dirname(self)"""
        return self._wrap(path.dirname(self))
        
    def exists(self):
        """os.path.exists(self)"""
        return path.exists(self)
    
    def join(self, *dirs):
        """os.path.join(self, *dirs)"""
        return self._wrap(path.join(self, *dirs))
    
    def mkdir(self, name):
        """makes a directory in the root and returns its full path.
        
        the path is split each non-existant directory is made.  
        returns full path to new directory.
        
        """
        # force it into an relative path...
        if name.startswith(os.path.sep):
            name = name[len(os.path.sep):]
            
        path = self.join(name)
        mkdirall(path)
        return path
    
    def normpath(self):
        """os.path.normpath(self)"""
        return self._wrap(path.normpath(self))
    
    def putfile(self, fname, contents, mode=None):
        """puts new filename relative to your `TempIO` root.
        Makes all directories along the path to the final file.
        
        returns absolute filename.
        """
        relpath, fname = split(fname)
        if relpath and not self.join(relpath).exists():
            if relpath.startswith(os.path.sep):
                relpath = relpath[1:]
            self.mkdir(relpath)
            
        f = self.join(relpath, fname)
        putfile(f, contents, mode=mode)
        return f
    
    def realpath(self):
        """os.path.realpath(self)"""
        return self._wrap(path.realpath(self))
    
    def splitext(self):
        """os.path.splitext(self)"""
        return path.splitext(self)
    
    def splitpath(self):
        """os.path.split(self)
        """
        return path.split(self)

class DeletableDirPath(DirPath):
    def __del__(self):
        """removes the root directory and everything under it.
        """
        if hasattr(self, '_deferred') and self._deferred:
            # atexit will handle it ...
            return
        try:
            _expunge(self)
        except:
            # means atexit didn't get it and there was some other exception
            # due to the unpredictable state of python's destructors; there is
            # nothing really to do
            pass
        