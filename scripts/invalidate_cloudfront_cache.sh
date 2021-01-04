#!/bin/bash
# only use this when it is urgend to get the docs updated. regular update time is 24h
aws cloudfront create-invalidation --distribution-id E3LWSA9IT755ZP --paths "/*" --profile bptk-website