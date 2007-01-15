
from nose.tools import with_setup, eq_
from fixture import DataSet
from fixture.dataset import DataRow, SuperSet, MergedSuperSet

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

class DataSetTest:
    """tests behavior of a DataSet object."""
    def assert_access(self, dataset):
        raise NotImplementedError
    def assert_row_dict_for_iter(self, items, count):
        raise NotImplementedError
    def assert_itered_n_times(count):
        raise NotImplementedError
    
    def test_access(self):
        self.assert_access(self.dataset)

    def test_iter_yields_keys_rows(self):
        count=0
        for k, row in self.dataset:
            count += 1
            items = dict([(k,v) for k,v in row.items()])
            self.assert_row_dict_for_iter(items, count)
        
        self.assert_itered_n_times(count)

class TestDataSet(DataSetTest):
    def setUp(self):
        self.dataset = Books()
    
    def assert_access(self, dataset):
        eq_(dataset.lolita.title, 'lolita')
        eq_(dataset.pi.title, 'life of pi')
        eq_(dataset['lolita'].title, 'lolita')
        eq_(dataset['pi'].title, 'life of pi')
    
    def assert_itered_n_times(self, count):
        eq_(count, 2)
    
    def assert_row_dict_for_iter(self, items, count):        
        if count == 1:
            eq_(items, {'title': 'lolita'})
        elif count == 2:
            eq_(items, {'title': 'life of pi'})
        else:
            raise ValueError("unexpected row %s, count %s" % (items, count))

class TestDataSetCustomMeta(DataSetTest):
    def setUp(self):
        # a dataset with a config that doesn't inherit from
        # the default config.  should be ok
        class Chairs(DataSet):
            class Meta:
                storage = 'PretendStorage'
            def data(self):
                return (
                    ('recliner', dict(type='recliner')),
                    ('Lazy-boy', dict(type='Lazy-boy'))
                )
        self.dataset = Chairs()
    
    def assert_access(self, dataset):
        eq_(dataset.recliner.type, 'recliner')
        eq_(dataset['Lazy-boy'].type, 'Lazy-boy')
        
        # should also have the same defaults as DataSet :
        eq_(dataset.meta.storage, 'PretendStorage')
        eq_(dataset.meta.row, DataSet.Meta.row)
        eq_(dataset.meta.loader, DataSet.Meta.loader)
    
    def assert_itered_n_times(self, count):
        eq_(count, 2)
    
    def assert_row_dict_for_iter(self, items, count):        
        if count == 1:
            eq_(items, {'type': 'recliner'})
        elif count == 2:
            eq_(items, {'type': 'Lazy-boy'})
        else:
            raise ValueError("unexpected row %s, count %s" % (items, count))
    
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
        