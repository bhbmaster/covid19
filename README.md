# covid19.py

The source code for the project located here: http://www.infotinks.com/coronavirus-dashboard-covid19-py/

Requirements:

* python 3.7 (or which ever python 3 allows for f"formatted strings {like} this")

* plotly python module. if missing can download+install with pip like so:
pip install plotly


* internet access to https://pomber.github.io/covid19/timeseries.json (more info about the timeseries here: https://github.com/pomber/covid19)


Just run *plot.py*. This will gather data, and parse it and generate directory html_plots/ and dump 2 graphs for each country (normal y axes and log y axes) in dir. As Total worldwide is not provided in time series, we have to calculate it from the data for each day from all countries. It will provide both plots for TOTAL in the same dir as well. It then creates covid19-log.html and covid19-normal.html in the root directory for all of the countries, TOTAL at the top, then sorted by number of cases.

If you want to run this on a schedule, I recommend running it after midnight each day as the timeseries data updates once a day. On my infotinks site it runs 3 times a day 00:05, 06:05, 12:05, 18:05 using crontab.
