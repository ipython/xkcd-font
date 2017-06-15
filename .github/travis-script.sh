#!/usr/bin/env bash

set -x

docker pull pelson/fontbuilder; 

echo "Generating font" 
xkcd-script/generator/run.sh; 

echo "Generating samples"; 
xkcd-script/samples/preview.sh; 

echo "Pushing back to repo"; 
.github/commit-and-push-from-travis.sh; 
