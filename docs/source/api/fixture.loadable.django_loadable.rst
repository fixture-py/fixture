------------------------------------------
:mod:`fixture.loadable.django_loadable`
------------------------------------------

.. automodule:: fixture.loadable.django_loadable


.. autoclass:: DjangoEnv
   
   .. automethod:: get


.. autoclass:: fixture.loadable.django_loadable.DjangoFixture
   :show-inheritance:
   :members: create_transaction, then_finally, attach_storage_medium
   
   Django's transaction management is implemented as a module, which is returned by :meth:`create_transaction`. This means the the :meth:`~fixture.loadable.loadable.DBLoadableFixture.commit` and :meth:`~fixture.loadable.loadable.DBLoadableFixture.rollback` remain unchanged from :class:`fixture.loadable.loadable.DBLoadableFixture`.
   
   As far as mapping DataSets to models, if you don't supply an env kwarg you'll get the :class:`~DjangoEnv` class. This simply provides a :meth:`get method <DjangoEnv.get>` that proxies through to :meth:`django.db.models.get_model`.
   Alternatively you can use an inner :class:`Meta <fixture.dataset.DataSetMeta>` with the following attribute:

   .. attribute:: django_model

    Use this on an inner :class:`Meta <fixture.dataset.DataSetMeta>` class to specify the model.
    It must be of a form that can be passed to ``get_model`` after being split on a ``'.'`` e.g:

    .. code-block:: python

        class Meta:
            django_model = 'auth.User'

.. autoclass:: fixture.loadable.django_loadable.DjangoMedium
   :show-inheritance:
   
   For now we're going to say that a Fixture can only define relations
   and fields defined locally to the target model. So given the :ref:`example models <django-models>`, Where Book has a ForeignKey to Author, then you'll have a fixture like:

   .. code-block:: python

      class app__Book(DataSet):
         class book1:
            # ...
            author = app__Author.some_author
                    
   and not like this:
   
   .. code-block:: python
   
      class app__Author(DataSet):
         class author1:
            # ...
            books = [app__Book.book1, app__Book.book2]
         
   .. note:: This might change in future as it looks like it should be possible to be able to do it the other way round (if desirable).
   
   .. automethod:: save
   
      Validates first with :meth:`_check_schema`
   
   .. automethod:: _check_schema
   
      .. note:: see the internal function ``column_vals`` inside :meth:`fixture.loadable.LoadableFixture.load_dataset` for more info
   
      .. warning:: This will check the field names and related model types only - it won't validate field types
      
      See the :ref:`example models <django-models>`

