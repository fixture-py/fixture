from decimal import Decimal

from fixture.dataset.converter import *
from fixture.test import attr
from nose.tools import eq_, raises
from six import StringIO


try:
    import json
except ImportError:
    import simplejson as json


class FooData(DataSet):
    class bar:
        name = "call me bar"
        is_alive = False

    class foo:
        name = "name's foo"
        is_alive = True


class MuchoData(DataSet):
    class mucho:
        d = datetime.date(2008, 1, 1)
        dt = datetime.datetime(2008, 1, 1, 2, 30, 59)
        dec = Decimal("1.45667")
        fl = float(1.45667)


class DummyError(Exception):
    pass


class TestDatasetToJson(object):
    @attr(unit=1)
    @raises(TypeError)
    def test_must_be_dataset(self):
        class NotADataSet(object):
            pass

        dataset_to_json(NotADataSet)

    def _sorted_eq(self, a, b, msg=None):
        eq_(sorted(a), sorted(b), msg)

    @attr(unit=1)
    def test_convert_cls(self):
        self._sorted_eq(
            dataset_to_json(FooData),
            json.dumps(
                [{
                    'name': "call me bar",
                    'is_alive': False,
                     },
                 {
                     'name': "name's foo",
                     'is_alive': True,
                     }]
            )
        )

    @attr(unit=1)
    def test_convert_instance(self):
        foo = FooData()
        self._sorted_eq(
            dataset_to_json(foo),
            json.dumps(
                [{
                     'name': "call me bar",
                     'is_alive': False
                     },
                 {
                     'name': "name's foo",
                     'is_alive': True
                     }]
            )
        )

    @attr(unit=1)
    def test_dump_to_file(self):
        fp = StringIO()
        dataset_to_json(FooData, fp=fp)
        self._sorted_eq(
            fp.getvalue(),
            json.dumps(
                [{
                     'name': "call me bar",
                     'is_alive': False
                     },
                 {
                     'name': "name's foo",
                     'is_alive': True
                }]
            )
        )

    @attr(unit=1)
    def test_types(self):
        self._sorted_eq(
            json.loads(dataset_to_json(MuchoData)),
            [{
                'd': "2008-01-01",
                "dt": "2008-01-01 02:30:59",
                "dec": "1.45667",
                "fl": 1.45667
            }]
        )

    @attr(unit=1)
    @raises(DummyError)
    def test_custom_converter(self):
        def my_default(obj):
            raise DummyError()

        ds = dataset_to_json(MuchoData, default=my_default)
        assert not ds, (
            "dataset_to_json() should have died but it returned: %s" % ds)

    @attr(unit=1)
    def test_wrap(self):
        def wrap_in_dict(objects):
            return {'data': objects}

        self._sorted_eq(
            dataset_to_json(FooData, wrap=wrap_in_dict),
            json.dumps({
                'data':
                    [{
                         'name': "call me bar",
                         'is_alive': False
                         },
                     {
                         'name': "name's foo",
                         'is_alive': True
                         }]
            })
        )
