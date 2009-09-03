
# profile for running tests as complete as possible
export FIXTURE_TEST_LITE_DSN="sqlite:///:memory:"
export FIXTURE_TEST_HEAVY_DSN="postgres://$USER@localhost/$USER"

# some django setup stuff
## is this solved by the NoseDjango plugin?
# export PYTHONPATH=../../test_loadable/test_django:$PYTHONPATH
# export DJANGO_SETTINGS_MODULE='project.settings'