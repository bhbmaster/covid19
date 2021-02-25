#!/bin/bash
# This script calls the covid19plot.py to generate the 2 plot html files
# it logs its text output to run-DATE.out files
# Then places.sh is called which uses run*out output to generate the places.html
# This also runs county-plot.py and logs its output to usa-ca this generates `usa-ca/county-output.html`
# How to run: adjust the cd parameter to root location of project + and use python 3.7 (or newer) to call the script
# I call this from crontab to generate my graphs for infotinks.com (runs every day at 00:05, 06:05, 12:05 and 18:05):
# 5 0,6,12,18 * * * /var/www/covid19/run.sh
PYTHON="python3.7"
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
DATE=`date +%Y%m%d-%H%M%S`
echo "Logging to $PWD/run-$DATE.out"
# run covid19plot.py to generate all data
echo "`date` - start" | tee -a run.timelog > run-$DATE.out
$PYTHON covid19plot.py >> run-$DATE.out 2>&1
echo "`date` - end" | tee -a run.timelog >> run-$DATE.out
# run places
./places.sh
# run california plots
cd "$DIR"/usa-ca
$PYTHON county-plot.py >> run-$DATE.out 2>&1
exit 0
