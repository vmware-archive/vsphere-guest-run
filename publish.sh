#!/usr/bin/env bash

rm -rf vsphere_guest_run/*.pyc
rm -rf build dist
python setup.py develop
python setup.py sdist bdist_wheel
twine upload dist/*
