#!/bin/bash
docker build --no-cache -t covid19 .
docker run -it --rm --name covid19dev covid19 /bin/bash
