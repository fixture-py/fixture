"""This is mostly a copy of methods and internal classes from loadable"""
from django.apps import apps
from fixture.loadable.loadable import DeferredStoredObject


def assert_empty(app_label):
    app = apps.get_app_config(app_label)
    for model in app.get_models():
        model_count = model.objects.count()
        assert model_count == 0, \
            'Found {} instances of {}'.format(model_count, model)


def resolve_stored_object(column_val):
    if type(column_val) == DeferredStoredObject:
        return column_val.get_stored_object_from_loader(self)
    else:
        return column_val


def get_column_vals(row):
    for c in row.columns():
        yield (c, resolve_stored_object(getattr(row, c)))
