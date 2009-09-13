#!/usr/bin/env bash

source fixture/test/profile/full.sh
# also see setup.cfg for more options

make -C docs doctest

# there is a bug in zc.buildout which needs to 
# be fixed before make will exit non-zero
# https://bugs.launchpad.net/zc.buildout/+bug/164629/
if [ $? -ne 0 ]; then
    exit $?
fi

# this is created by bin/buildout:
./bin/test-fixture