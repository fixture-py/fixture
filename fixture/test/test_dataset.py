
from nose.tools import with_setup, eq_
from fixture import DataSet, DataRow, SuperSet, MergedSuperSet

class Books(DataSet):
    def data(self):
        return (
            ('lolita', dict(title='lolita')),
            ('pi', dict(title='life of pi')),
        )

class Movies(DataSet):
    def data(self):
        return (
            ('peewee', dict(director='Tim Burton')),
            ('aquatic', dict(director='cant remember his name')),
        )

class TestDataSet:
    def setUp(self):
        self.dataset = Books()
    
    def test_access(self):
        eq_(self.dataset.lolita.title, 'lolita')
        eq_(self.dataset.pi.title, 'life of pi')
        eq_(self.dataset['lolita'].title, 'lolita')
        eq_(self.dataset['pi'].title, 'life of pi')

    def test_iter_yields_keys_rows(self):
        count=0
        for k, row in self.dataset:
            count += 1
            items = dict([(k,v) for k,v in row.items()])
            if count == 1:
                eq_(items, {'title': 'lolita'})
            elif count == 2:
                eq_(items, {'title': 'life of pi'})
            else:
                raise ValueError("unexpected row %s, count %s" % (row, count))
    
        eq_(count, 2)
    
class SuperSetTest:
    """tests common behavior of SuperSet like objects."""
    SuperSet = None
    
    def setUp(self):
        self.superset = self.SuperSet(Books(), Movies())
    
    def test_access(self):
        raise NotImplementedError
    
    def test_iter_yields_datasets(self):
        count=0
        for ds in self.superset:
            count += 1
            if count == 1:
                eq_(ds.lolita.title, 'lolita')
            elif count == 2:
                eq_(ds.peewee.director, 'Tim Burton')
            else:
                raise ValueError("unexpected row %s, count %s" % (ds, count))
        eq_(count, 2)

class TestSuperSet(SuperSetTest):
    SuperSet = SuperSet
    
    def test_access(self):
        eq_(self.superset.Books.lolita.title, 'lolita')
        eq_(self.superset.Books.pi.title, 'life of pi')
        eq_(self.superset.Books['lolita'].title, 'lolita')
        eq_(self.superset.Books['pi'].title, 'life of pi')
        eq_(self.superset['Books']['lolita'].title, 'lolita')
        eq_(self.superset['Books']['pi'].title, 'life of pi')

class TestMergedSuperSet(SuperSetTest):
    SuperSet = MergedSuperSet
    
    def test_access(self):
        eq_(self.superset.lolita.title, 'lolita')
        eq_(self.superset.pi.title, 'life of pi')
        eq_(self.superset['lolita'].title, 'lolita')
        eq_(self.superset['pi'].title, 'life of pi')
        eq_(self.superset.peewee.director, 'Tim Burton')
        eq_(self.superset.aquatic.director, 'cant remember his name')
        