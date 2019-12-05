# How to build BPTK-Py

## What you need

- Valid login for test.pypi.org
- Valid login for official PyPi.org
- Logged in to Docker Hub (``docker login``) and Rights to push to ```transentis/bptk-py``` repo!

**Please increase the release number in [../conf.py](../conf.py) before starting!!**

## How we build

Core of the process is [publish.sh](publish.sh). It tests, builds and publishes BPTK-Py in one go.

To make sure all requirements are sufficient and all tests pass in a fresh Python environment, the process contains multiple steps.

1. Create a virtual ENV and run tests inside it for the current build version
2. Generate Distribution
3. Upload to test.pypi.org (Login required)
4. Install into a venv from test.pypi.org and run tests
5. Upload to official PyPi (Login required)
6. Create docker image with current version and tag the latest version

## How to start

Just execute [publish.sh](publish.sh) in this directory. During execution you will be asked for login data for the different services.



