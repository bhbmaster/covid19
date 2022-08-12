#!/bin/bash
# This will download the latest Dockerfile and build-and-run.sh script
# and kick off build-and-run.sh to enter you into a covid19 build environment container.
# Required to have a working docker environment.
# The README.md on the root of the project has a command of how to run all of this in one go with curl and bash
# Recommend to run from an empty directory, so you can see what it downloads
curl -o Dockerfile https://raw.githubusercontent.com/bhbmaster/covid19/master/dev-docker-env/Dockerfile
curl -o build-and-run.sh https://raw.githubusercontent.com/bhbmaster/covid19/master/dev-docker-env/build-and-run.sh
chmod +x build-and-run.sh
./build-and-run.sh
