#!/bin/bash

# just run plot scripts (logs shown on terminal and not saved)
# recommended to run from MAC however it will work on any system where python3 points at a supported version of python with all of the required modules (see README.md)

PYTHON="python3"
( cd usa-ca; $PYTHON county-plot.py )
( $PYTHON covid19plot.py )