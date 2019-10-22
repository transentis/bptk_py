#!/bin/sh
cd ..
git submodule update --recursive --remote
rm -rf BPTK_Py/sd-compiler/node_modules/
python3 setup.py sdist bdist_wheel

