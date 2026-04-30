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

## Local pre-flight publish script.
##
## Architecture note (see docs/internal/architecture/rust-engine-packaging.md):
##   bptk-py is now a maturin-built package containing both the Python sources
##   and the Rust engine (BPTK_Py._rust_engine). Production releases are cut by
##   tagging vX.Y.Z and letting .github/workflows/publish.yml build the full
##   platform-wheel matrix (Linux x86_64+aarch64, macOS x86_64+aarch64,
##   Windows x86_64) plus the sdist, and upload to PyPI via trusted publishing.
##
##   This script CANNOT produce that matrix — manylinux, aarch64 and Windows
##   wheels require their own runners. What it can do, and what it does:
##     1. Run the test suite locally against an editable install.
##     2. Build the sdist + a current-platform wheel via maturin.
##     3. Upload them to Test PyPI.
##     4. Re-run the tests against the Test PyPI install to catch packaging
##        regressions (missing files, broken extension load, etc.).
##     5. Stop. Final PyPI publish is the CI workflow's job; tag the release.

set -e

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
pip install python-dotenv
# pip install -e . triggers a maturin PEP 517 build, compiling the Rust
# extension into the venv. Requires a working Rust toolchain locally.
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
echo "Generating Distribution (sdist + current-platform wheel)"
echo "-------------------------------------"
echo "NOTE: cross-platform wheels are produced by .github/workflows/publish.yml,"
echo "      not here. This local build is for Test PyPI smoke-testing only."

pip install twine
pip install maturin
rm -rf dist/
# Current-platform wheel for local validation against Test PyPI.
maturin build --release --out dist
# Universal sdist (fallback for users on platforms with no published wheel).
maturin sdist --out dist


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
echo "Running tests against Test-PyPi Version"
echo "-------------------------------------"

echo "Waiting a few seconds so PyPi can index the new version"
sleep 8
python3 -m venv venv_temp
source ./venv_temp/bin/activate
pip install pytest
pip install python-dotenv
# Pull bptk-py from Test PyPI; deps come from real PyPI.
pip install --index-url https://test.pypi.org/simple/ bptk_py --extra-index-url https://pypi.org/simple

# Sanity check: the Rust extension must load on this platform.
python3 -c "from BPTK_Py import _rust_engine; print('Rust engine loaded:', _rust_engine)"

if ! pytest ./; then
    echo "Tests failed! Not continuing. Please fix your code"
    deactivate
    rm -rf venv_temp/
    exit 1
fi
deactivate
rm -rf venv_temp/
rm -f ./tests/test_models/*.py

echo "-------------------------"
echo "All Test PyPI checks passed."
echo ""
echo "Final PyPI publish is handled by GitHub Actions (publish.yml)."
echo "To cut the release, push a tag:"
echo "    git tag vX.Y.Z && git push origin vX.Y.Z"
echo "CI will then build wheels for Linux x86_64+aarch64, macOS x86_64+aarch64,"
echo "Windows x86_64, plus the sdist, and upload them via trusted publishing."
echo "-------------------------"

rm -rf dist/
rm -rf build/
rm -rf BPTK_Py.egg-info
