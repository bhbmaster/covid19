#!/bin/bash
# This script calls the covid19plot.py to generate the 2 plot html files
# it logs its text output to run-DATE.out files
# Then places.sh is called which uses run*out output to generate the places.html
# How to run: adjust the cd parameter to root location of project + and use python 3.7 (or newer) to call the script
# I call this from crontab to generate my graphs for infotinks.com (runs every day at 00:05, 06:05, 12:05 and 18:05):
# 5 0,6,12,18 * * * /var/www/covid19/run.sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /var/www/covid19
DATE=`date +%Y%m%d-%H%M%S`
echo "Logging to $PWD/run-$DATE.out"
echo "`date` - start" | tee -a run.timelog > run-$DATE.out
python3.7 covid19plot.py >> run-$DATE.out 2>&1
echo "`date` - end" | tee -a run.timelog >> run-$DATE.out
# run places
./places.sh
exit 0
