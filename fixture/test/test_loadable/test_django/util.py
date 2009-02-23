"""This is mostly a copy of methods and internal classes from loadable"""

from django.db.models.loading import get_models
from fixture.loadable.loadable import DeferredStoredObject

def assert_empty(mod):
    for model in get_models(mod):
        assert model.objects.count() == 0

def resolve_stored_object(column_val):
    if type(column_val)==DeferredStoredObject:
        return column_val.get_stored_object_from_loader(self)
    else:
        return column_val

def get_column_vals(row):
    for c in row.columns():
        yield (c, resolve_stored_object(getattr(row, c)))