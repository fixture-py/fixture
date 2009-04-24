#!/usr/bin/env bash

source fixture/test/profile/full.sh
# also see setup.cfg for more options

pushd docs
make doctest
popd

# -i includes for pylons example app
nosetests -i source -i examples -i pylons_example -i addressbook

# NoseGAE does not work in virtualenv but it would be nice of it did \
# -i google_appengine_example \
# --with-gae
