# covid19.py

The source code for the project located here: http://www.infotinks.com/coronavirus-dashboard-covid19-py/

covid19plot.py produces the following graphs:
- Normal Axes: http://www.infotinks.com/covid19/covid19-normal.html
- Log Axes: http://www.infotinks.com/covid19/covid19-log.html

I use a wrapper script run.sh to run covid19plot.py and save its text output to log files (run-$DATE.out)
Then places.sh uses those log files to get ordered list of most cases for each day. The output is saved in this html file:
- Places: http://www.infotinks.com/covid19/places.html

Requirements:

* python 3.7 or newer (or which ever python 3 allows for f"formatted strings {like} this")

* plotly python module. if missing can download+install with pip like so:
pip install plotly

* internet access to https://pomber.github.io/covid19/timeseries.json (more info about the timeseries here: https://github.com/pomber/covid19)

Just run *covid10plot.py* with python3.7 or newer, that will gather data, parse it and generate directory html_plots/ and dump 2 graphs for each country (normal y axes and log y axes) in dir. As Total worldwide cases/recovery/deaths is not provided in the json time series, the script manually calculates from the data for each day by summing through all of the countries. It will provide both plots for TOTAL in the same dir as well. It then creates covid19-log.html and covid19-normal.html in the root directory for all of the countries, TOTAL at the top, then sorted by number of cases.

Update: I commented out the html_plots/ output as it generated 2.5 MiB for each country (2 times; one for log graph and one for normal graph). Its easier to just look at covid19-log.html and covid19-normal.html which has everything and is much smaller. 

If you want to run this on a schedule, I recommend running it after midnight each day as the timeseries data updates once a day. On my infotinks site it runs 3 times a day 00:05, 06:05, 12:05, 18:05 using crontab. It run run.sh which runs covid19plot.sh saves the output to run-$DATE.out and then run places.sh. The then generates for me covid19-log.html, covid19-normal.html and places.html.
