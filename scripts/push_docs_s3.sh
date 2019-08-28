#!/bin/bash
# build the docs first with "make html"
# aws access controls need to be set - call "aws configure" if these are not set
aws s3 cp ../_build/html s3://bptk.transentis-labs.com/en/latest --recursive --acl public-read
