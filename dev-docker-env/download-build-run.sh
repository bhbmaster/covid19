#!/bin/bash

# This will download the latest Dockerfile and build-and-run.sh script
# and kick off build-and-run.sh to enter you into a covid19 build environment container.
# Required to have a working docker environment.
# The README.md on the root of the project has a command of how to run all of this in one go with curl and bash
# Recommend to run from an empty directory, so you can see what it downloads
# The command is:
# curl https://raw.githubusercontent.com/bhbmaster/covid19/master/dev-docker-env/download-build-run.sh | tr -d '\r' | bash

curl -o Dockerfile https://raw.githubusercontent.com/bhbmaster/covid19/master/dev-docker-env/Dockerfile
curl -o build-and-run.sh https://raw.githubusercontent.com/bhbmaster/covid19/master/dev-docker-env/build-and-run.sh
chmod +x build-and-run.sh
# ./build-and-run.sh # can't run piped from wget to bash as it complained about missing TTY
# which is okay as we want to 2 step it regardless. Step 1 download. Step 2 run command to build and run.
echo "** Run command below to start the covid19 development environment ***"
echo "./build-and-run.sh"
