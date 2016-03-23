from nose.tools import eq_

from fixture import DataSet
from fixture.dataset import (
    Ref, DataRow, SuperSet, MergedSuperSet, is_rowlike)
from fixture.test import attr


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


class Authors(DataSet):
    class martel:
        name = 'Yann Martel'

    class nabokov:
        name = 'Vladimir Nabokov'


class BooksAndAuthors(DataSet):
    class lolita:
        title = 'lolita'
        author = Authors.nabokov.ref('name')

    class pi:
        title = 'life of pi'
        author = Authors.martel.ref('name')


class CategoryData(DataSet):
    class vehicles:
        id = 1
        name = 'cars'

    class free_stuff:
        id = 2
        name = 'get free stuff'

    class discounted:
        id = 3
        name = 'discounted stuff'


class ProductData(DataSet):
    class truck:
        id = 1
        name = 'truck'
        category_id = CategoryData.vehicles.ref('id')

    class spaceship:
        id = 2
        name = 'spaceship'
        category_id = CategoryData.vehicles.ref('id')


class OfferData(DataSet):
    class free_truck:
        id = 1
        name = "it's a free truck"
        product_id = ProductData.truck.ref('id')
        category_id = CategoryData.free_stuff.ref('id')

    class discounted_spaceship:
        id = 2
        name = "it's a spaceship 1/2 off"
        product_id = ProductData.spaceship.ref('id')
        category_id = CategoryData.discounted.ref('id')


class DataSetTest:
    """tests behavior of a DataSet object."""

    def assert_access(self, dataset):
        raise NotImplementedError

    def assert_row_dict_for_iter(self, items, count):
        raise NotImplementedError

    def assert_itered_n_times(count):
        raise NotImplementedError

    @attr(unit=True)
    def test_access(self):
        self.assert_access(self.dataset)

    @attr(unit=True)
    def test_iter_yields_keys_rows(self):
        count = 0
        for k, row in self.dataset:
            count += 1
            items = dict([(k, getattr(row, k)) for k in row.columns()])
            self.assert_row_dict_for_iter(k, items, count)

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

    def assert_row_dict_for_iter(self, key, items, count):
        if count == 1:
            eq_(items, {'title': 'lolita'})
        elif count == 2:
            eq_(items, {'title': 'life of pi'})
        else:
            raise ValueError("unexpected row %s, count %s" % (items, count))


class TestDataRow(object):
    @attr(unit=True)
    def test_datarow_is_rowlike(self):
        class StubDataSet(DataSet):
            pass

        row = DataRow(StubDataSet)
        assert is_rowlike(row), "expected %s to be rowlike" % row


class TestDataTypeDrivenDataSet(TestDataSet):
    def setUp(self):
        class Books(DataSet):
            class lolita:
                title = 'lolita'

            class pi:
                title = 'life of pi'

        self.dataset_class = Books
        self.dataset = Books()

    @attr(unit=True)
    def test_row_is_decorated_with_ref(self):
        assert hasattr(self.dataset_class.lolita, 'ref'), (
            "expected %s to be decorated with a ref method" %
            self.dataset_class.lolita)
        assert self.dataset_class.lolita.ref.__class__ == Ref, (
            "unexpected ref class: %s" %
            self.dataset_class.lolita.ref.__class__)

    @attr(unit=True)
    def test_row_is_rowlike(self):
        assert is_rowlike(self.dataset_class.lolita), (
            "expected %s to be rowlike" % self.dataset_class.lolita)


@attr(unit=True)
def test_is_rowlike():
    class StubDataSet(DataSet):
        class some_row:
            pass

    class StubDataSetNewStyle(DataSet):
        class some_row(object):
            pass

    eq_(is_rowlike(StubDataSet.some_row), True)
    eq_(is_rowlike(StubDataSetNewStyle.some_row), True)
    eq_(is_rowlike(DataRow(StubDataSet)), True)

    class StubRow:
        pass

    class StubRowNewStyle(object):
        pass

    eq_(is_rowlike(StubRow), False)
    eq_(is_rowlike(StubRowNewStyle), False)

    eq_(is_rowlike(1), False)
    eq_(is_rowlike({}), False)
    eq_(is_rowlike([]), False)


class InheritedRowsTest(DataSetTest):
    def assert_access(self, dataset):
        def assert_all_attr(type):
            fxt = getattr(dataset, type)
            eq_(fxt.type, type)
            eq_(fxt.session, 'aaaaaaa')
            eq_(fxt.offer, 1)
            eq_(fxt.time, 'now')

        assert_all_attr('click')
        assert_all_attr('submit')
        assert_all_attr('order')
        assert_all_attr('activation')

    def assert_itered_n_times(self, count):
        eq_(count, 4)

    def assert_row_dict_for_iter(self, key, items, count):
        if count == 1:
            eq_(items,
                {
                    'offer': 1, 'time': 'now', 'session': 'aaaaaaa',
                    'type': 'activation'
                    })
        elif count == 2:
            eq_(items,
                {
                    'offer': 1, 'time': 'now', 'session': 'aaaaaaa',
                    'type': 'click'
                    })
        elif count == 3:
            eq_(items,
                {
                    'offer': 1, 'time': 'now', 'session': 'aaaaaaa',
                    'type': 'order'
                    })
        elif count == 4:
            eq_(items,
                {
                    'offer': 1, 'time': 'now', 'session': 'aaaaaaa',
                    'type': 'submit'
                    })
        else:
            raise ValueError("unexpected row %s at key %s, count %s" % (
                items, key, count))


class EventData(DataSet):
    class click:
        type = 'click'
        session = 'aaaaaaa'
        offer = 1
        time = 'now'

    class submit(click):
        type = 'submit'

    class order(click):
        type = 'order'

    class activation(click):
        type = 'activation'


class TestInheritedRows(InheritedRowsTest):
    dataset = EventData()


class EventDataNewStyle(DataSet):
    class click(object):
        type = 'click'
        session = 'aaaaaaa'
        offer = 1
        time = 'now'

    class submit(click):
        type = 'submit'

    class order(click):
        type = 'order'

    class activation(click):
        type = 'activation'


class TestInheritedRowsWithNewStyle(InheritedRowsTest):
    dataset = EventDataNewStyle()


class TestDataSetCustomMeta(DataSetTest):
    def setUp(self):
        # a dataset with a config that doesn't inherit from
        # the default config.  should be ok
        class Chairs(DataSet):
            class Meta:
                storable_name = 'PretendStorage'

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
        eq_(dataset.meta.storable_name, 'PretendStorage')
        eq_(dataset.meta.row, DataSet.Meta.row)

    def assert_itered_n_times(self, count):
        eq_(count, 2)

    def assert_row_dict_for_iter(self, key, items, count):
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

    @attr(unit=True)
    def test_access(self):
        raise NotImplementedError

    @attr(unit=True)
    def test_iter_yields_datasets(self):
        count = 0
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

    @attr(unit=True)
    def test_access(self):
        eq_(self.superset.Books.lolita.title, 'lolita')
        eq_(self.superset.Books.pi.title, 'life of pi')
        eq_(self.superset.Books['lolita'].title, 'lolita')
        eq_(self.superset.Books['pi'].title, 'life of pi')
        eq_(self.superset['Books']['lolita'].title, 'lolita')
        eq_(self.superset['Books']['pi'].title, 'life of pi')


class TestMergedSuperSet(SuperSetTest):
    SuperSet = MergedSuperSet

    @attr(unit=True)
    def test_access(self):
        eq_(self.superset.lolita.title, 'lolita')
        eq_(self.superset.pi.title, 'life of pi')
        eq_(self.superset['lolita'].title, 'lolita')
        eq_(self.superset['pi'].title, 'life of pi')
        eq_(self.superset.peewee.director, 'Tim Burton')
        eq_(self.superset.aquatic.director, 'cant remember his name')


class ComplexRefTest:
    @attr(unit=True)
    def test_construction(self):
        eq_(self.offer_data.meta.references, [CategoryData, ProductData])
        eq_(self.product_data.meta.references, [CategoryData])

        cat_data = self.product_data.meta.references[0]()
        eq_(cat_data.meta.references, [])
        eq_([c.__class__ for c in self.product_data.ref], [CategoryData])


class TestComplexRefs(ComplexRefTest):
    def setUp(self):
        self.offer_data = OfferData()
        self.product_data = ProductData()


class ProductObj(DataSet):
    class truck:
        category_id = CategoryData.vehicles

    class spaceship:
        category_id = CategoryData.vehicles


class OfferObj(DataSet):
    class free_truck:
        product = ProductData.truck
        category = CategoryData.free_stuff

    class discounted_spaceship:
        product = ProductData.spaceship
        category = CategoryData.discounted


class TestComplexRefsToObjects(ComplexRefTest):
    def setUp(self):
        self.offer_data = OfferObj()
        self.product_data = ProductObj()


class ProductObjList(DataSet):
    class truck:
        categories = [CategoryData.vehicles]

    class spaceship:
        categories = [CategoryData.vehicles]


class OfferObjList(DataSet):
    class free_truck:
        products = [ProductData.truck]
        categories = [CategoryData.free_stuff]

    class discounted_spaceship:
        products = [ProductData.spaceship]
        categories = [CategoryData.discounted]


class TestComplexRefsToListsOfObjects(ComplexRefTest):
    def setUp(self):
        self.offer_data = OfferObjList()
        self.product_data = ProductObjList()


class ProductObjTuple(DataSet):
    class truck:
        categories = tuple([CategoryData.vehicles])

    class spaceship:
        categories = tuple([CategoryData.vehicles])


class OfferObjTuple(DataSet):
    class free_truck:
        products = tuple([ProductData.truck])
        categories = tuple([CategoryData.free_stuff])

    class discounted_spaceship:
        products = tuple([ProductData.spaceship])
        categories = tuple([CategoryData.discounted])


class TestComplexRefsToTuplesOfObjects(ComplexRefTest):
    def setUp(self):
        self.offer_data = OfferObjTuple()
        self.product_data = ProductObjTuple()


@attr(unit=True)
def test_DataSet_cant_add_refs_to_self():
    class Pals(DataSet):
        class henry:
            name = 'Henry'
            buddy = None

        class jenny:
            name = "Jenny"

        jenny.buddy = henry

    # will also create an infinite loop :
    ds = Pals()
    eq_(ds.meta.references, [])
