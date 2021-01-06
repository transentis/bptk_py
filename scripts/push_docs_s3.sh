#!/bin/bash
# build the docs first with "make html"
# aws access controls need to be set - call "aws configure" if these are not set
# credentials of bptk-website user in production environment are needed
aws s3 cp ../_build/html s3://bptk.transentis.com/en/latest --recursive --acl  public-read --profile bptk-website
