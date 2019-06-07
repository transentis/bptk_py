#!/bin/bash
cd ..
#twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*
rm -rf dist/
rm -rf build/
rm -rf BPTK_Py.egg-info