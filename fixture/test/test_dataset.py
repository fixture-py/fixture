
from nose.tools import with_setup, eq_
from fixture import DataSet, DataRow

dataset = None

class BooksByAttr(DataSet):
    def data(self):
        return (
            ('lolita', dict(title='lolita')),
            ('pi', dict(title='life of pi')),
        )

def clear_dataset():
    global dataset
    dataset = None

def with_dataset(d):
    def activate_set():
        global dataset
        dataset = d()
    return with_setup(activate_set, clear_dataset)

@with_dataset(BooksByAttr)
def test_access():
    eq_(dataset.lolita.title, 'lolita')
    eq_(dataset.pi.title, 'life of pi')
    eq_(dataset['lolita'].title, 'lolita')
    eq_(dataset['pi'].title, 'life of pi')

@with_dataset(BooksByAttr)
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
        