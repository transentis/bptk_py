#!/bin/bash

cd /home/
node -r babel-register src/cli.js -i $1 -t py > $2