from datetime import datetime

from django.db import models as django_models
from fixture import DjangoFixture
from fixture.loadable.django_loadable import field_is_required
from fixture.test.test_loadable.test_django.fixtures import \
    InvalidNoRelationsData
from fixture.test.test_loadable.test_django.fixtures import ValidNoRelationsData
from fixture.test.test_loadable.test_django.util import get_column_vals
from nose.tools import raises


def _check_row(medium, column_vals):
    medium._check_schema(column_vals)


def test_schema_conformance():
    valid_rels = ValidNoRelationsData()
    invalid_rels = InvalidNoRelationsData()

    class NoRelations(django_models.Model):
        char = django_models.CharField(max_length=10)
        num = django_models.IntegerField()

        class Meta:
            app_label = 'tests'

    for dataset, model, callable in \
        [
            (valid_rels, NoRelations, _check_row),
            (invalid_rels, NoRelations,
             raises(ValueError)(_check_row))
        ]:
        djm = DjangoFixture.Medium(NoRelations, dataset)
        rows = [(row[0], list(get_column_vals(row[1]))) for row in dataset]
        for row in rows:
            callable.description = "schema.conformance: %s %s in %s" % (
            row[0], row[1],
            dataset.__class__.__name__)
            yield callable, djm, row[1]


def test_is_field_required():
    from django.db import models
    class TestMod(models.Model):

        pk = models.CharField(primary_key=True)
        req = models.CharField()
        default_char = models.CharField(default='default_val')
        null = models.CharField(null=True)
        date = models.DateTimeField(auto_now=True)
        req_date = models.DateTimeField()
        nullable_date = models.DateTimeField(null=True, auto_now_add=True)
        default_date = models.DateTimeField(default=datetime.now)

        class Meta:
            app_label = 'tests'

    required_matrix = dict(
        pk=False,
        req=True,
        default_char=False,
        null=False,
        date=False,
        req_date=True,
        nullable_date=False,
        default_date=False,
    )

    def check_field_required(fld, result):
        msg = "field '%s': null=%s, primary_key=%s, auto_now=%s, " \
              "auto_now_add=%s " \
              "should be %s"
        auto_now = getattr(fld, 'auto_now', None)
        auto_now_add = getattr(fld, 'auto_now_add', None)
        assert field_is_required(fld) == result, msg % (fld.name, fld.null,
                                                        fld.primary_key,
                                                        auto_now, auto_now_add,
                                                        result)

    for item in required_matrix.items():
        fld, result = item
        check_field_required.description = "%s required? %s" % item
        yield check_field_required, TestMod._meta.get_field(fld), result
