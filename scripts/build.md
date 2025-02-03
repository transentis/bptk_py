# How to build BPTK-Py

## What you need

- Valid login for test.pypi.org
- Valid login for official PyPi.org
- Logged in to Docker Hub (``docker login``) and Rights to push to ```transentis/bptk-py``` repo!

## Before building

### Install build requirements

1. Make sure you have the basic build tools on your machine. We need ``make`` which is usually included in your Linux distro. Mac OS X may require some extra installations.
2. Run ``pip install -r requirements-dev.txt`` inside the main directory of this repo.
3. Install docker on your machine if you want to create Docker containers and publish to dockerhub. Run ``docker login`` to login to Dockerhub using your account credentials. Obtain access rights for the ``transentis/bptk-py`` repo from the admin.
4. Get an account for [pypi.org](https://pypi.org) as well as [test.pypi.org](https://test.pypi.org) and become a maintainer for the BPTK_Py package.

## How we build

__Please increase the release number in [../setup.py](../setup.py) before starting!!__

Core of the process is [publish.sh](publish.sh). It tests, builds and publishes BPTK-Py in one go.

To make sure all requirements are sufficient and all tests pass in a fresh Python environment, the process contains multiple steps.

1. Create a virtual ENV and run tests inside it for the current build version
2. Generate Distribution
3. Upload to test.pypi.org (login credentials configured in ~/.pypirc)
4. Install into a venv from test.pypi.org and run tests
5. Upload to official PyPi (Login credentials configured in ~/.pypirc)

Just execute ``make publish_bptk`` in the root directory of the repo.

WARNING: Make sure you start the process from an activated venv with Python version >=3.11

## Publish to Docker

For building the docker container, we are now providing a new Python script. It uses Python's lowlevel API for Docker. 
Hence, for building, tagging and publishing to docker, run ``make publish_docker`` in the root directory of the repo.

## Build and Publish documentation

To build the documentation, run ``make html`` in the root directory of the repository. 

The resulting documentation is then copied into the documentation repository on GitHub. As soon as the branch is pushed this rebuilds the website on DigitalOcean.


```
make html
make publish_docu
```



