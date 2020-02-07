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

Just execute ``make publish_bptk`` inthe root directory of the repo.

## Publish to Docker

For building the docker container, we are now providing a new Python script. It uses Python's lowlevel API for Docker. 
Hence, for building, tagging and publishing to docker, run ``make publish_docker`` in the root directory of the repo

## Build and Publish documentation

To build the documentation, run ``make html`` in the root directory of the repository. 
A subsequent ```make publish_docu``` publishes it to S3. It will take some time for the changes to reflect on the website 
as we are using CloudFront as a CDN. It usually updates its caches within 24 hours.


```
make html
make publish_docu
```



