# -*- coding: latin_1 -*-

import os
from nose.tools import eq_
from os.path import join, exists, isdir, basename
from os import path
from copy import copy
from nose.tools import eq_, raises
from fixture import TempIO
from fixture.io import mkdirall, putfile

french = "tu pense qu'on peut m'utiliser comme ça?"

def test_mkdirall():
    tmp = TempIO()
    cwd = os.getcwd()
    try:
        mkdirall(join(tmp.root, 'blah/blah/'))
        assert exists(join(tmp.root, 'blah/blah'))
        
        # relative too ...
        os.chdir(tmp.root)
        mkdirall('ici/ou/la')
        assert exists('ici')
        assert exists('ici/ou')
        assert exists('ici/ou/la')
        
    finally:
        del tmp
        os.chdir(cwd)

def test_putfile():
    tmp = TempIO()
    cwd = os.getcwd()
    try:
    
        fname = join(tmp.root, 'french.txt')
        putfile(fname, french)
    
        assert exists(fname)
    
        f = open(fname, 'r')
        contents = f.read()
        f.close()
        assert contents == french
        
        # can make lazy dirs ..
        fname = join(tmp.root, 'ou/est/tu/frenchy.txt')
        putfile(fname, "")
        assert exists(fname)
        
        # relative :
        os.chdir(tmp.root)
        putfile('bahh', '')
        assert exists(join(tmp.root, 'bahh'))
        
    finally:
        del tmp
        os.chdir(cwd)

def test_del_self_destructs():
    """asserts that a module level reference self destructs 
    without exception."""
    global _TMP
    _TMP = TempIO()

class TestTempIO(object):
    def setUp(self):
        self.tmp = TempIO()
    
    def tearDown(self):
        if hasattr(self, 'tmp'):
            del self.tmp
    
    def test_deferred(self):
        self.tmp = TempIO(deferred=True)
        root = self.tmp.root
        assert exists(root)
        del self.tmp
        assert exists(root)
    
        self.tmp = TempIO(deferred=False)
        root = self.tmp.root
        assert exists(root)
        del self.tmp
        assert not exists(root)

    def test_del(self):
        root = copy(self.tmp.root)
        del self.tmp
        assert not exists(root)

    def test_keywords(self):
        self.tmp_custom = TempIO(prefix='foobar_', dir=self.tmp.root)
        try:
            assert exists(join(self.tmp.root, basename(self.tmp_custom.root)))
            assert basename(self.tmp_custom.root).startswith('foobar_')
        finally:
            del self.tmp_custom

    def test_mkdir(self):
        base1 = self.tmp.mkdir('base1')
        assert exists(join(self.tmp.root, base1))
        base2 = self.tmp.mkdir('base2')
        assert exists(join(self.tmp.root, base2))

    def test_newdir(self):
        self.tmp.rick_james = "rick_james"
        assert exists(self.tmp.rick_james)
        assert self.tmp.rick_james.startswith(self.tmp.root)
        assert self.tmp.rick_james.endswith("rick_james")
        
        self.tmp.rick_james = "rick james"
        assert exists(self.tmp.rick_james)
        assert self.tmp.rick_james.startswith(self.tmp.root)
        assert self.tmp.rick_james.endswith("rick james")
        
        self.tmp.rick_james = "rick_james/i/love/you"
        assert exists(self.tmp.rick_james)
        assert self.tmp.rick_james.startswith(self.tmp.root)
        assert self.tmp.rick_james.endswith("rick_james/i/love/you")
    
    def test_path_interface(self):
        self.tmp.dupes = "processed/dupes"
        def endswith(p, end):
            assert p.endswith(end), "%s did not end in %s" % (p,end)
        
        eq_(self.tmp.dupes, path.join(self.tmp.root, "processed/dupes"))
        eq_(self.tmp.dupes.abspath(), 
                path.abspath(path.join(self.tmp.root, "processed/dupes")))
        eq_(self.tmp.dupes.basename(), "dupes")
        eq_(self.tmp.dupes.dirname(), path.join(self.tmp.root, "processed"))
        eq_(self.tmp.dupes.exists(), True)
        eq_(self.tmp.dupes.join("foo", "bar"), path.abspath(path.join(
                                    self.tmp.root, "processed/dupes/foo/bar")))
        eq_(self.tmp.dupes.join("foo", "bar").exists(), False)
        self.tmp.more_dupes = self.tmp.dupes.join("foo", "bar")
        eq_(self.tmp.dupes.join("foo", "bar").exists(), True)
        
        eq_(self.tmp.dupes.realpath(), 
                path.realpath(path.join(self.tmp.root, "processed/dupes")))
        eq_(self.tmp.dupes.split(), 
                (path.realpath(path.join(self.tmp.root, "processed")), "dupes"))
        eq_(self.tmp.dupes.splitext(), (path.realpath(path.join(self.tmp.root, 
                                                    "processed/dupes")), ""))        

    @raises(ValueError)
    def test_newdir_root(self):
        # can't name a property "root" :
        self.tmp.root = 'root'

    def test_putfile(self):
        self.tmp.putfile('frenchy.txt', french)

        assert exists(join(self.tmp.root, 'frenchy.txt'))
        assert open(join(self.tmp.root, 'frenchy.txt'), 'r').read() == french

        abspath = self.tmp.putfile('petite/grenouille/frenchy.txt', french)
        exppath = join(self.tmp.root, 'petite/grenouille/frenchy.txt')
        assert exists(exppath)
        eq_(abspath, exppath)

        # check laziness of putfile's mkdir'ing :
        self.tmp.putfile('petite/grenouille/ribbit/frenchy.txt', french)
        assert exists(join(self.tmp.root, 
                            'petite/grenouille/ribbit/frenchy.txt'))
        
    def test_putfile_mode(self):
        self.tmp.putfile('frenchy.txt', "", 'wb')
        f = open(join(self.tmp.root, 'frenchy.txt'), 'rb')
        f.read()

    def test_root(self):
        assert isdir(self.tmp.root)
    