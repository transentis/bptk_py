#!/bin/bash
# PARAMS: SCRIPT_HOME IN OUT
CURRENT_HOME="$PWD"
cd $1

node -r babel-register src/cli.js -i "$CURRENT_HOME/$2" -t py -c > "$CURRENT_HOME/$3"