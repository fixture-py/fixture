------------------------------------------
fixture.django_testcase
------------------------------------------

.. automodule:: fixture.django_testcase

.. autoclass:: fixture.django_testcase.FixtureTestCase
    :show-inheritance:
    :members: _fixture_setup, _fixture_teardown

    .. attribute:: datasets

        This is a list of :class:`DataSets <fixture.dataset.DataSet>` that will be created and destroyed for each test method.
        The result of setting them up will be referenced by the :attr:`data`

    .. attribute:: data

        Any :attr:`datasets` found are loaded and refereneced here for later teardown
