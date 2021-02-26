#!/bin/bash
# This uses run*out log output files to generate the places.html.
# So run.sh had to be run several times over course of days to get good values run-$DATE.out files
# place.sh shows each countries place (of most cases) at any given date
# Ex: we can see that China was 1st place but then US over took it in March
# Adjust cd to location where your root directory for this project is
# This script is called from run.sh but it can be run standalone as well.
# -- CLEAN UP COMMANDS --
# For this script to work we need good run-DATE.out files 
# Good ones end with "- end", so lets look for all of the run.*out files that have it and don't have it
# Then we can manually delete them:
# # for i in run*out; do grep -q -- "- end" $i && echo "Found at $i" || echo "Missing at $i"; done | grep -v Found
# Result is all of the run files missing good data, and therefore can be deleted as they are not parsable
cd /var/www/covid19
(
   N=$(cat $(ls -1tr | grep run.*out | tail -1) | grep "/" | tail -1 | cut -f 1 -d "/")
   [ -z $N ] && N=10
   echo "<p><b>Which country is Xth place at given date (started from 3/15/2020)</b></p>";
   for i in $(seq $N); do
      (
         P=$((i-1))
         echo "---- $P place ----";
         grep "^$i/" run* | awk -F " - " '{$1=""; print "*"$0}' | uniq
      )  |  awk '{print "<p>" $0 "</p>"}'
   done
) > places.html
