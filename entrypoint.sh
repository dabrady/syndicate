#!/usr/bin/env sh

# TODO Can we programmatically match Dockerfile?
WORKDIR=/action
cd $WORKDIR
"$WORKDIR"/src/helloworld.py $@
