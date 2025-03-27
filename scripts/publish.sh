#!/bin/bash

#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

## MAGIC Build Script that also tests your code!


#pip3 install -r ../requirements-dev.txt

#git submodule update --remote --recursive

#######################
## Run tests locally ##
#######################

echo "-------------------------------------"
echo "Running tests on local version"
echo "-------------------------------------"

cd ..
python3 -m venv venv_temp
source ./venv_temp/bin/activate
pip install pytest
pip install -e .

if ! pytest ./ ; then
    echo "Tests failed! Not continuing. Please fix your code"
    deactivate
    rm -rf venv_temp/
    exit 1
fi
deactivate
rm -rf venv_temp/


###################
## Generate Dist ##
###################

echo "-------------------------------------"
echo "Generating Distribution"
echo "-------------------------------------"


pip install twine
pip install build
python3 -m build --sdist
python3 -m build --wheel


## Upload to Test PyPi
echo "-------------------------------------"
echo "Uploading to Test-PyPi!"
echo "-------------------------------------"
if ! twine upload --verbose --repository bptk-py-test dist/* ; then
  echo "Upload to Test PyPi failed! Aborting"
  rm -rf dist/
  rm -rf build/
  rm -rf BPTK_Py.egg-info
  exit 1
fi


####################################
## Run tests against PyPi version ##
####################################

echo "-------------------------------------"
echo "Running tests against PyPi Version"
echo "-------------------------------------"

echo "Waiting a few seconds so PyPi can index the new version"
sleep 8
python3 -m venv venv_temp
source ./venv_temp/bin/activate
pip install pytest
pip install --index-url https://test.pypi.org/simple/ bptk_py --extra-index-url https://pypi.org/simple

if ! pytest ./; then
    echo "Tests failed! Not continuing. Please fix your code"
    deactivate
    rm -rf venv_temp/
    exit 1
fi
deactivate
rm -rf venv_temp/
rm ./tests/test_models/*.py

echo "-------------------------"
echo "All tests successful!"
echo "Proceeding with upload to actual Pypi"
echo "-------------------------"
##################################
## Push to official PyPi Mirror ##
##################################


if ! twine upload --verbose --repository bptk-py dist/* ; then
  echo "Upload to PyPi failed! Aborting. Please retry!"
  rm -rf dist/
  rm -rf build/
  rm -rf BPTK_Py.egg-info
  exit 1
fi

rm -rf dist/
rm -rf build/
rm -rf BPTK_Py.egg-info


