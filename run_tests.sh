#!/usr/bin/env bash

source fixture/test/profile/full.sh
# also see setup.cfg for more options

make -C docs doctest

# this is created by bin/buildout:
./bin/test-fixture