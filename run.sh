#!/bin/bash
# This script just calls the plot script to generate the 2 plot html files and places.sh to generate the places.html
# How to run: adjust the cd parameter and python3.7 call to match your python 3.7 location
# I call this from crontab to generate my graphs for infotinks.com
# 5 0,6,12,18 * * * /var/www/covid19/run.sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /var/www/covid19
DATE=`date +%Y%m%d-%H%M%S`
echo "`date` - start" | tee -a run.timelog > run-$DATE.out
python3.7 covid19plot.py >> run-$DATE.out 2>&1
echo "`date` - end" | tee -a run.timelog >> run-$DATE.out
# run places
./places.sh
exit 0
