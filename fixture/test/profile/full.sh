
# profile for running tests as complete as possible
export FIXTURE_TEST_LITE_DSN="sqlite:///:memory:"
export FIXTURE_TEST_HEAVY_DSN="postgres://$USER@localhost/$USER"