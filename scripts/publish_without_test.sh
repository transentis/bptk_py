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



###################
## Generate Dist ##
###################


echo "-------------------------------------"
echo "Generating Distribution"
echo "-------------------------------------"
cd ..

pip install twine
pip install build
python3 -m build --sdist
python3 -m build --wheel

##################################
## Push to official PyPi Mirror ##
##################################

echo ""
echo "Uploading to PyPi"

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


rm -rf dist/
rm -rf build/
rm -rf BPTK_Py.egg-info

#echo "-------------------------------------"
#echo "Docker publish"
#echo "-------------------------------------"
#python3 build_docker.py

#echo "-------------------------------------"
#echo "Publication done!"
#echo "-------------------------------------"
