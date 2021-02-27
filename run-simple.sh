#!/bin/bash
# just run plot scripts (logs shown on terminal and not saved)
( cd usa-ca; python county-plot.py )
( python covid19plot.py )