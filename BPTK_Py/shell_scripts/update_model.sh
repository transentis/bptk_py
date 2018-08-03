#!/bin/bash
# PARAMS: SCRIPT_HOME IN OUT
CURRENT_HOME="$PWD"
echo "$CURRENT_HOME"
cd $1
#IN_LOC = "$CURRENT_HOME/$2"
#OUT_LOC ="$CURRENT_HOME/$3"
echo "$CURRENT_HOME/$2"
node -r babel-register src/cli.js -i "$CURRENT_HOME/$2" -t py -c > "$CURRENT_HOME/$3"