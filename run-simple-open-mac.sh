#!/bin/bash

# for mac: just run plots and opens covid19-normal.html & county-output.html in browser when done
# logs shown on terminal and not saved

( cd usa-ca; python county-plot.py && open county-output.html )
( python covid19plot.py && open covid19-normal.html )