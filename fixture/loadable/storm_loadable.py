
"""Components for loading and unloading data using `Storm`_.

See :ref:`Using LoadableFixture<using-loadable-fixture>` for examples.

.. _Storm: https://storm.canonical.com/

"""

from fixture.loadable import DBLoadableFixture
from fixture.util import _mklog

stlog = _mklog('fixture.loadable.storm')

class StormMedium(DBLoadableFixture.StorageMediumAdapter):

    def clear(self, obj):
        self.transaction.remove(obj)

    def save(self, row, column_vals):
        from storm.info import get_cls_info
        from storm.locals import ReferenceSet, Store

        cls_info = get_cls_info(self.medium)

        column_vals = list(column_vals)
        pk = []
        for n, v in column_vals:
            propid = id(getattr(self.medium, n))
            if propid in cls_info.primary_key_idx:
                pk.append((cls_info.primary_key_idx[propid], v, n))

        assert len(pk) == 0 or len(pk) == len(cls_info.primary_key), (
            "Incomplete primary key see %s need %s" % (
                [x[2] for x in pk], [x.name for x in cls_info.primary_key]))

        if pk:
            obj = self.transaction.get(self.medium, tuple([x[1] for x in sorted(pk)]))
        else:
            obj = None

        if obj is None:
            obj = self.medium()
            self.transaction.add(obj)

        assert Store.of(obj) is self.transaction

        for n, v in column_vals:
            if isinstance(getattr(self.medium,n), ReferenceSet):
                getattr(obj, n).add(v)
            else:
                setattr(obj, n, v)

        self.transaction.flush()
        stlog.info("%s %s", obj, [(n,getattr(obj,n)) for n in row.columns()])

        return obj

    def visit_loader(self, loader):
        """Visit the loader and store a reference to the transaction connection"""
        self.transaction = loader.transaction


    pass

class StormFixture(DBLoadableFixture):
    StormMedium = StormMedium
    Medium = StormMedium

    def __init__(self,  store=None, use_transaction=True, 
                        close_store=False, **kw ):
        DBLoadableFixture.__init__(self, **kw)
        self.store = store
        self.close_store = close_store
        self.use_transaction = use_transaction

    def create_transaction(self):
        return self.store



    pass
