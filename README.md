# covid19plot.py

The public facing version of this site sits on my personal blog at **infotinks.com**: http://www.infotinks.com/coronavirus-dashboard-covid19-py/

**covid19plot.py produces the following graphs:**

- Normal Axes plot of every country in one file: http://www.infotinks.com/covid19/covid19-normal.html

- Log Axes plot of every country in one file: http://www.infotinks.com/covid19/covid19-log.html

- Each country generates its own seperate normal and log plot into the `html-plots/` directory. As these are smaller the browser has an easier time allowing interaction with these plots

Example: 

```
html-plots/US-plot-NORMAL.html
html-plots/US-plot-LOG.html
```

**usa-ca/county-plot.py produces the following graphs:**

- Daily New Cases in all California countys plotted to `usa-ca/county-output.html`

## Wrapper run.sh Scrip & places.sh

I use a wrapper script `run.sh` to execute covid19plot.py which generates both of the html files to same directory - while also logging any terminal output to a log file, `run-$DATE.out` (this output is used by a log parser tool I call places.sh). It also runs `usa-ca/county-plot.py` which generates `usa-ca/county-output.html` and redirects its logout to `usa-ca/run-$DATE.out`

Then my `places.sh` uses those log files to get ordered list of most cases for each day. For any given date, one can see which country ranks amongst highest cases. The output is saved in this html file:

- Places: http://www.infotinks.com/covid19/places.html

## Requirements

* View requirements.txt to see the required python modules

* Tested with Python 3.7 and 3.9 - but probably works with Python 3.6 and higher (as we use f strings introduced)

* Internet access (see Other Requirements below)

## Required Python Module

The required python modules can be installed using pip.

* Install all modules like so:

        pip install -r requirements.txt

Or install the modules listed in `requirements.txt` one by one using `pip install <module>`

## Other Requirements

* Internet access to https://pomber.github.io/covid19/timeseries.json 

More info about the timeseries is available directly from the github address: https://github.com/pomber/covid19

## Execute Program - Running The Program - Generating The Output Data

Just run `covid19plot.py` with `python3.7` or newer, that will gather data, parse it and generate directory html_plots/ and dump 2 graphs for each country (normal y axes and log y axes) in dir. As Total worldwide cases/recovery/deaths is not provided in the json time series, the script manually calculates from the data for each day by summing through all of the countries. It will provide both plots for TOTAL in the same dir as well. It then creates covid19-log.html and covid19-normal.html in the root directory for all of the countries, TOTAL at the top, then sorted by number of cases.

If you want to run this on a schedule, I recommend running it after midnight each day as the timeseries data updates once a day. On my infotinks site it runs 3 times a day 00:05, 06:05, 12:05, 18:05 using crontab. It executes `run.sh` which runs `covid19plot.sh` and saves the output to `run-$DATE.out` and then it run `places.sh` (to generate the extra places document). All of this generates the output files `covid19-log.html`, `covid19-normal.html` and `places.html` which are linked to from my infotinks site.

To run (the python program hooks to python 3.7):

```bash
python covid19plot.py
```

Or:

```bash
./run.sh &
tail -F <log file>
```
    
* Space Requirements: after all of the plots generate the project directory total size might be around 1.2 to 1.5 GiB in size.

## How To Prepare VirtualEnv Environment

First create a python3 virtual environment and install the modules like so:

```bash
cd <into root directory where covid19plot.py is>
python3 -v venv env
source env/bin/activate
pip install -r requirements.txt
```

Then run the script using the above execute instructions.

## Errors

Possible errors that might be seen:

### Missing _bz2 On Linux

If you get an error during running `usa-ca/county-plot.py` which talks about missing _bz2 module. Then you will need install a linux package and compile python again & you will need to reinstall the python modules with pip.

* Error notes: https://stackoverflow.com/questions/12806122/missing-python-bz2-module
* Compiling new python: https://linuxize.com/post/how-to-install-python-3-9-on-debian-10/

### Other Errors

Might need to google your way around or contact me via "Issues" tab
