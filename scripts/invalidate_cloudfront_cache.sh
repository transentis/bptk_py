#!/bin/bash
# only use this when it is urgend to get the docs updated. regular update time is 24h
aws cloudfront create-invalidation --distribution-id EMYYIG5K526NL --paths "/*"