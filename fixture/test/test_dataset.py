
from nose.tools import with_setup, eq_
from fixture import DataSet, DataRow, SuperSet, MergedSuperSet

dataset = None

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

def clear_dataset():
    global dataset
    dataset = None

def with_dataset(d):
    def activate_set():
        global dataset
        dataset = d
    return with_setup(activate_set, clear_dataset)

@with_dataset(Books())
def test_dataset_access():
    eq_(dataset.lolita.title, 'lolita')
    eq_(dataset.pi.title, 'life of pi')
    eq_(dataset['lolita'].title, 'lolita')
    eq_(dataset['pi'].title, 'life of pi')
    
@with_dataset(SuperSet(Books()))
def test_superset_access():
    eq_(dataset.Books.lolita.title, 'lolita')
    eq_(dataset.Books.pi.title, 'life of pi')
    eq_(dataset.Books['lolita'].title, 'lolita')
    eq_(dataset.Books['pi'].title, 'life of pi')
    eq_(dataset['Books']['lolita'].title, 'lolita')
    eq_(dataset['Books']['pi'].title, 'life of pi')
    
@with_dataset(MergedSuperSet(Books(), Movies()))
def test_superset_access():
    eq_(dataset.lolita.title, 'lolita')
    eq_(dataset.pi.title, 'life of pi')
    eq_(dataset['lolita'].title, 'lolita')
    eq_(dataset['pi'].title, 'life of pi')
    eq_(dataset.peewee.director, 'Tim Burton')
    eq_(dataset.aquatic.director, 'cant remember his name')

@with_dataset(Books())
def test_iter_dataset():
    count=0
    for k, row in dataset:
        count += 1
        if count == 1:
            eq_(row.__dict__, {'title': 'lolita'})
        elif count == 2:
            eq_(row.__dict__, {'title': 'life of pi'})
        else:
            raise ValueError("unexpected row %s, count %s" % (row, count))
    
    eq_(count, 2)

@with_dataset(SuperSet(Books(), Movies()))
def test_iter_superset():
    count=0
    for k, ds in dataset:
        count += 1
        if count == 1:
            eq_(k, 'Books')
            eq_(ds.lolita.title, 'lolita')
        elif count == 2:
            eq_(k, 'Movies')
            eq_(ds.peewee.director, 'Tim Burton')
        else:
            raise ValueError("unexpected row %s, count %s" % (row, count))
    eq_(count, 2)
        