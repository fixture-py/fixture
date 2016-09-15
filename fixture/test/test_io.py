# -*- coding: latin_1 -*-

import os
from nose.tools import eq_
from os.path import join, exists, isdir, basename
from os import path
from copy import copy
from nose.tools import eq_, raises
from fixture import TempIO
from fixture.io import mkdirall, putfile
from fixture.test import attr

french = "tu pense qu'on peut m'utiliser comme ça?"

@attr(unit=True)
def test_mkdirall():
    tmp = TempIO()
    cwd = os.getcwd()
    try:
        mkdirall(join(tmp, 'blah/blah/'))
        assert exists(join(tmp, 'blah/blah'))
        
        # relative too ...
        os.chdir(tmp)
        mkdirall('ici/ou/la')
        assert exists('ici')
        assert exists('ici/ou')
        assert exists('ici/ou/la')
        
    finally:
        del tmp
        os.chdir(cwd)

@attr(unit=True)
def test_putfile():
    tmp = TempIO()
    cwd = os.getcwd()
    try:
    
        fname = join(tmp, 'french.txt')
        putfile(fname, french)
    
        assert exists(fname)
    
        f = open(fname, 'r')
        contents = f.read()
        f.close()
        assert contents == french
        
        # can make lazy dirs ..
        fname = join(tmp, 'ou/est/tu/frenchy.txt')
        putfile(fname, "")
        assert exists(fname)
        
        # relative :
        os.chdir(tmp)
        putfile('bahh', '')
        assert exists(join(tmp, 'bahh'))
        
    finally:
        del tmp
        os.chdir(cwd)

@attr(unit=True)
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
    
    @attr(unit=True)
    def test_deferred(self):
        tmp = TempIO(deferred=True)
        root = str(tmp)
        assert exists(root)
        del tmp
        assert exists(root)
    
        tmp2 = TempIO(deferred=False)
        root = str(tmp2)
        assert exists(root)
        del tmp2
        assert not exists(root)

    @attr(unit=True)
    def test_del(self):
        root = copy(self.tmp)
        del self.tmp
        assert not exists(root)

    @attr(unit=True)
    def test_keywords(self):
        self.tmp_custom = TempIO(prefix='foobar_', dir=self.tmp)
        try:
            assert exists(join(self.tmp, basename(self.tmp_custom)))
            assert basename(self.tmp_custom).startswith('foobar_')
        finally:
            del self.tmp_custom

    @attr(unit=True)
    def test_mkdir(self):
        base1 = self.tmp.mkdir('base1')
        assert exists(join(self.tmp, base1))
        base2 = self.tmp.mkdir('base2')
        assert exists(join(self.tmp, base2))

    @attr(unit=True)
    def test_newdir(self):
        self.tmp.rick_james = "rick_james"
        assert exists(self.tmp.rick_james)
        assert self.tmp.rick_james.startswith(self.tmp)
        assert self.tmp.rick_james.endswith("rick_james")
        
        self.tmp.rick_james = "rick james"
        assert exists(self.tmp.rick_james)
        assert self.tmp.rick_james.startswith(self.tmp)
        assert self.tmp.rick_james.endswith("rick james")
        
        self.tmp.rick_james = "rick_james/i/love/you"
        assert exists(self.tmp.rick_james)
        assert self.tmp.rick_james.startswith(self.tmp)
        assert self.tmp.rick_james.endswith("rick_james/i/love/you")
    
    @attr(unit=True)
    def test_path_interface(self):
        self.tmp.dupes = "processed/dupes"
        def endswith(p, end):
            assert p.endswith(end), "%s did not end in %s" % (p,end)
        
        eq_(self.tmp.dupes, path.join(self.tmp, "processed/dupes"))
        eq_(self.tmp.dupes.abspath(), 
                path.abspath(path.join(self.tmp, "processed/dupes")))
        eq_(self.tmp.dupes.basename(), "dupes")
        eq_(self.tmp.dupes.dirname(), path.join(self.tmp, "processed"))
        eq_(self.tmp.dupes.normpath(), path.normpath(self.tmp.dupes))
        eq_(self.tmp.dupes.exists(), True)
        eq_(self.tmp.dupes.join("foo", "bar"), path.abspath(path.join(
                                    self.tmp, "processed/dupes/foo/bar")))
        eq_(self.tmp.dupes.join("foo", "bar").exists(), False)
        
        self.tmp.dupes.more = "foo/bar"
        eq_(path.exists(path.join(self.tmp.dupes, "foo", "bar")), True)
        eq_(self.tmp.dupes.join("foo", "bar").exists(), True)
        
        eq_(self.tmp.dupes.realpath(), 
                path.realpath(path.join(self.tmp, "processed/dupes")))
        eq_(self.tmp.dupes.splitpath(), path.split(self.tmp.dupes))
        eq_(self.tmp.dupes.splitext(), (path.realpath(path.join(self.tmp, 
                                                    "processed/dupes")), ""))

    @attr(unit=True)
    def test_putfile(self):
        self.tmp.putfile('frenchy.txt', french)

        assert exists(join(self.tmp, 'frenchy.txt'))
        assert open(join(self.tmp, 'frenchy.txt'), 'r').read() == french

        abspath = self.tmp.putfile('petite/grenouille/frenchy.txt', french)
        exppath = join(self.tmp, 'petite/grenouille/frenchy.txt')
        assert exists(exppath)
        eq_(abspath, exppath)

        # check laziness of putfile's mkdir'ing :
        self.tmp.putfile('petite/grenouille/ribbit/frenchy.txt', french)
        assert exists(join(self.tmp, 
                            'petite/grenouille/ribbit/frenchy.txt'))
        # make sure that a second call will only create directories necessary:
        self.tmp.putfile('petite/grenouille/ribbit/foo.txt', "foo")
        
    @attr(unit=True)
    def test_putfile_mode(self):
        self.tmp.putfile('frenchy.txt', b"", 'wb')
        f = open(join(self.tmp, 'frenchy.txt'), 'rb')
        f.read()
    
    @attr(unit=True)
    @raises(TypeError)
    def test_putfile_accepts_only_relative_paths(self):
        self.tmp.putfile('/petite/grenouille/ribbit/frenchy.txt', "franch")

    @attr(unit=True)
    def test_rmtree(self):
        root = str(self.tmp)
        self.tmp.rmtree()
        assert not exists(root)

    @attr(unit=True)
    def test_root(self):
        assert isdir(self.tmp)
    