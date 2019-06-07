#!/bin/sh
cd ..
rm -rf BPTK_Py/sd-compiler/node_modules/
python3 setup.py sdist bdist_wheel

