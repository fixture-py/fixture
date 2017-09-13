"""Components for loading and unloading data using
`Django's ORM <http://www.djangoproject.com>`_.

See :ref:`Using Fixture With Django <using-fixture-with-django>` for a
complete example.
"""

try:
    from django.apps.registry import apps
except ImportError:
    pass

from fixture.loadable import DBLoadableFixture
from fixture.loadable.loadable import EnvLoadableFixture
from fixture.util import any


__all__ = ('DjangoMedium', 'DjangoFixture', 'DjangoEnv')

DJANGO_ENV_SPLIT = '__'

pretty_model_name = lambda model: '.'.join([model._meta.app_label,
                                            model._meta.object_name])


def field_is_required(field):
    """Is this field required to have a value

    This is not the same as null=False, it needs to take account of
    auto_add, auto_now_add
    If any of the conditions not nullable, and not auto_now or auto_now_add are
    met then this should be true
    """
    from django.db.models.fields import NOT_PROVIDED
    if field.primary_key:
        return False
    fields = [field.null,
              field.default != NOT_PROVIDED,
              getattr(field, 'auto_now', False),
              getattr(field, 'auto_now_add', False)]
    return not any(fields)


class DjangoMedium(DBLoadableFixture.StorageMediumAdapter):
    """Adapter for storing data using django models
    """

    def clear(self, obj):
        """Delete this object from the DB

        :param obj: The object to delete
        :type obj: A django model
        """
        obj.delete()

    def _annotate_invalid_schema_exception(self, model, key):
        """Try and add more context to any error message"""
        info = ""
        related_objects = self._get_related_objects_for_model(model)
        fld_lookup = \
            {ro.field.related_query_name(): ro for ro in related_objects}
        try:  # Provide a nicer error message
            if key in fld_lookup:
                other_model = fld_lookup[key].model
                fld_name = fld_lookup[key].field.name
                info = ("\n**********************\n"
                        "This is a reverse relation of %s, you "
                        "should specifiy it there, i.e:\n"
                        "    %sData(DataSet):\n"
                        "        class ...:\n"
                        "            %s = [...]\n"
                        "**********************\n" %
                        ("%s.%s" % (pretty_model_name(other_model), fld_name),
                         other_model.__name__,
                         fld_name))
        except:
            pass
        return info

    @staticmethod
    def _get_related_objects_for_model(model):
        return [
            f for f in model._meta.get_fields(include_hidden=True)
            if (f.one_to_many or f.one_to_one or f.many_to_many)
               and f.auto_created
        ]

    def _check_schema(self, column_vals):
        """Check that the column_vals given match up to this model's schema

        :param column_vals: The parsed column values
        :type column_vals: tuple of field_name, field_value
        :raises: ValueError
        """

        model = self.medium
        # This will be only localy defined fields (excluding many_to_many)
        own_field_names = set([f.name for f in model._meta.fields])
        # All locally defined fields which are required and not auto fields (id)
        required_field_names = set([f.name for f in model._meta.fields
                                    if field_is_required(f)])
        m2m_field_names = set([f.name for f in model._meta.many_to_many])

        processed_column_values = []
        for key, val in column_vals:
            # Valid field?
            if not key in own_field_names.union(m2m_field_names):
                msg = "Model %r doesn't have field named %s." % \
                      (pretty_model_name(model), key)

                raise ValueError(msg +
                                 self._annotate_invalid_schema_exception(model,
                                                                         key))

            # Keep a track of required fields
            try:
                required_field_names.remove(key)
            except KeyError:
                pass

            # If the field is a relation check the related type
            field = model._meta.get_field(key)
            from django.db.models.fields.related import ManyToManyField
            if isinstance(field, ManyToManyField):
                try:
                    len(val)
                except TypeError:
                    val = [val]
                rel_types = [isinstance(v, field.rel.to) for v in val]
                if not field.null and False in rel_types:
                    raise ValueError("Values for field %s must be of type %s, "
                                     "got %s" %
                                     (key,
                                      pretty_model_name(field.rel.to),
                                      val))
            processed_column_values.append((key, val))
        if len(required_field_names):
            raise ValueError("Requred fields %s not found" %
                             required_field_names)
        return m2m_field_names, processed_column_values

    def save(self, row, column_vals):
        """Save this row to the DB"""
        model = self.medium
        manager = self.medium._default_manager
        field_names = [f.name for f in model._meta.fields]
        # column_vals = list(column_vals)
        m2m_field_names, column_vals = self._check_schema(column_vals)
        # This will take care of foreignkeys too
        dbvals = {}
        for key, val in column_vals:
            if key in field_names:
                dbvals[key] = val
        new_obj = manager.get_or_create(**dbvals)[0]
        columns = dict(column_vals)
        for m2m in m2m_field_names:
            if m2m in columns:
                getattr(new_obj, m2m).add(*columns[m2m])
        return new_obj

    def visit_loader(self, loader):
        """Let Django TestCase take care of transactions itself."""
        pass


class DjangoFixture(EnvLoadableFixture):
    Medium = DjangoMedium

    def attach_storage_medium(self, ds):
        model_identifier = getattr(ds.meta, 'django_model', None)
        if model_identifier:
            model = self._get_model(ds, model_identifier)
        else:
            model = super(DjangoFixture, self).attach_storage_medium(ds)
        return model

    def _get_model(self, data_store, model_identifier):
        try:
            app_label, model_name = model_identifier.split('.')
        except ValueError:
            raise ValueError(
                "Invalid django_model %r, expected "
                "'<app_label>.<model_name>'" % model_identifier)
        else:
            model = apps.get_app_config(app_label).get_model(model_name)
            if not model:
                raise self.StorageMediaNotFound(
                    "Django model %s not found" % model_identifier)
            data_store.meta.storage_medium = self.Medium(model, data_store)
            return model

    def wrap_in_transaction(self, routine, unloading=False):
        self.begin(unloading=unloading)
        try:
            routine()
        finally:
            self.then_finally(unloading=unloading)


class DjangoEnv(object):
    """
    A wrapper around get_models to allow lookup from DataSet's class name

    """

    @staticmethod
    def get(name, default=None):
        """Fetch this name from django's cache

        :param name: A name like app__ModelName such that name.split('__')
            will give you an app label and a model name suitable for get_model
        """
        from django.apps import apps

        try:
            app_label, model_name = name.split(DJANGO_ENV_SPLIT)
        except ValueError:
            raise ValueError(
                "DataSet class name %r must be a `%s' separated combination "
                "of app label "
                "and model name.  Alternatively, you can set "
                "Meta.django_app_label "
                "to match the DataSet class name to a model for that app." % (
                    name, DJANGO_ENV_SPLIT))
        else:
            try:
                model = apps.get_app_config(app_label).get_model(model_name)
            except LookupError:
                return None
            else:
                return model
