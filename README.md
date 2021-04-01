# covid19plot.py

The public facing version of this site sits on my personal blog at **infotinks.com**: http://www.infotinks.com/coronavirus-dashboard-covid19-py/

**covid19plot.py produces the following graphs:**

- Normal Axes plot of every country in one file - output: http://www.infotinks.com/covid19/covid19-normal.html

- Log Axes plot of every country in one file - output: http://www.infotinks.com/covid19/covid19-log.html

- Each country generates its own seperate normal and log plot into the `html-plots/` directory. As these are smaller the browser has an easier time allowing interaction with these plots

Example: 

```
html-plots/US-plot-NORMAL.html
html-plots/US-plot-LOG.html
```

**usa-ca/county-plot.py produces the following graphs and outputs:**

- Daily New Cases in all California countys plotted to `usa-ca/county-output.html` and `usa-ca/county-output-raw.html`
- Relative per Population Plot: http://www.infotinks.com/covid19/usa-ca/county-output.html
- Normal Plot: http://www.infotinks.com/covid19/usa-ca/county-output-raw.html
- `usa-ca/county-output.html` shows the values of the counties and California state relative to the population per 100K and with 7 day moving average
- `usa-ca/county-output-raw.html` shows the raw values of the counties and California state with 7 day moving average
- The moving average only applies to Daily New Cases & Daily New Deaths plots. The Total Cases & Total Deaths plot do not have the moving average function applied to them
- Also it generates the raw csv data that was downloaded `usa-ca/CA-covid19cases_test.csv` and then we manipulated it to a smaller more digestable and parsable table which is also saved `usa-ca/CA-covid19cases_test-parsable.csv`

**usa-states/county-plot.py produces the similar graphs and outputs:**

- Daily New Cases in all California countys plotted to `usa-states/states-output.html` and `usa-states/states-output-raw.html`
- Relative per Population Plot: http://www.infotinks.com/covid19/usa-states/states-output.html
- Normal Plot: http://www.infotinks.com/covid19/usa-states/states-output-raw.html
- `usa-states/states-output.html` shows the values of the States of the USA relative to the population per 100K and with 7 day moving average
- `usa-states/states-output-raw.html` shows the raw values of the States of the USA with 7 day moving average
- The moving average only applies to Daily New Cases & Daily New Deaths plots. The Total Cases & Total Deaths plot do not have the moving average function applied to them
- Also it generates the raw csv data that was downloaded `usa-states/us-states.csv` and then we manipulated so its a parsable table which is also saved `usa-states/us-states-parsable.csv`

## Wrapper run.sh Script & places.sh

The wrapper script `run.sh` execute `covid19plot.py` which generates both of the html files to same directory - while also logging any terminal output to a log file, `run-$DATE.out` (this output is used by a log parser tool I call places.sh). It also runs `usa-ca/county-plot.py` which generates `usa-ca/county-output.html` and redirects its logout to `usa-ca/run-$DATE.out`

Then my `places.sh` uses those log files to get ordered list of most cases for each day. For any given date, one can see which country ranks amongst highest cases. The output is saved in this html file:

- Places output: http://www.infotinks.com/covid19/places.html

*Sidenote:* The version of python is specified with the `PYTHON` variable at the beginning of the run.sh script. This is important for my linux server because the `python` program points to `python2.7` by default, so I must specify python 3 by using the `python3.x` program call (such as `python3.9`)

*Sidenote:* Created two wrapper scripts for `run.sh`, `run-wrapper.sh` & `run-and-pull-wrapper.sh`. One just kicks off `run.sh`, prints the PIDS, and follows the log. The latter updates the latest code from git using `git pull` and then kicks off `run.sh`, prints the PIDS and follows the log. Canceling the log follow, doesn't cancel the operation - you will need to kill the posted PIDs.

## Simple Wrapper Script

Run `run-simple-mac.sh` from root directory of the project and it will run `usa-ca/county-plot.py` and then `covid19plot.py`. Output is shown on terminal and not saved to run logs for parsing. This runs the faster script first, unlike the `run.sh` wrapper script which runs the lengthier plotter (covid19plot.py) first.

From a MAC run `run-simple-open-mac.sh` which runs the same two scripts and then opens the results in a default browser. This will work on MAC but probably not Windows or Linux as it uses `open <file>` program (if I am not mistaken that is only supported on MACs; for other OS need different program to launch files with their default application).

*Sidenote:* These scripts call the default python program using python. So if that calls `python2.7` for you, this script will fail. To fix that, you will need to edit the script to call `python3.x`, such as `python3.9`, instead just `python`.

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

## File Structure

Here are the dirs and files

```bash
covid19plot# ls --hide "run*" --hide "*html" -R -l

~~~.:~~~

-rwxr-xr-x 1 root root 42888 Mar  2 18:55 covid19plot.py        # main code - plots countrys and creates html output

-rw-r--r-- 1 root root 27340556 Mar  2 18:07 covid19-log.html     # log plots of country covid stats
-rw-r--r-- 1 root root 27338240 Mar  2 18:07 covid19-normal.html  # normal plots of country covid stats
-rw-r--r-- 1 root root  7189726 Mar  2 18:07 places.html          # ranking countries from highest to lowest cases each day

-rw-r--r-- 1 root root   646 Mar  2 00:35 PLOTLY_THEME          # theme file
-rw-r--r-- 1 root root  6155 Mar  1 22:10 README.md             # this readme
-rw-r--r-- 1 root root     9 Mar  2 10:26 VERSION               # version
-rwxr-xr-x 1 root root  1364 Feb 25 16:30 places.sh             # parses output files generated from run.sh & generates places.html 
-rw-r--r-- 1 root root    44 Feb 24 16:47 requirements.txt      # python requirements

-rwxr-xr-x 1 root root     1709 Mar  1 22:10 run.sh          # for infotinks server -  covid19plot.py and county-plot.py, creates run-$DATE-out log files, and runs place.sh (crontab calls this)
-rwxr-xr-x 1 root root      814 Mar  1 22:14 run-and-pull-wrapper.sh     # for infotinks server - sync code from git and kick off run.sh into background and follow log
-rwxr-xr-x 1 root root      688 Mar  1 22:14 run-wrapper.sh              # for infotinks server - kick off run.sh into background and follow log
-rw-r--r-- 1 root root    22166 Mar  2 10:28 run-$DATE.out  # several of these exist, output from run.sh parsed by places.sh


-rwxr-xr-x 1 root root      326 Mar  1 22:10 run-simple-mac.sh           # run code on mac 
-rwxr-xr-x 1 root root      268 Mar  1 22:10 run-simple-open-mac.sh      # run code on mac and open html plots

drwxr-xr-x 2 root root  4096 Mar  2 18:07 usa-ca                # where counties are
drwxr-xr-x 2 root root  4096 Mar  2 18:55 code                  # code dir
drwxr-xr-x 3 root root  4096 Feb 24 16:52 example-output        # example output           
drwxr-xr-x 2 root root 20480 Jan 22 06:11 html-plots            # where each countries log and normal plots go
drwxr-xr-x 2 root root  4096 Apr 14  2020 img-plots             # old dir, not used anymore (images too big). code is commented out

~~~./code:~~~
-rw-r--r-- 1 root root 8217593 Mar  2 18:55 CountryTestData.json      # test data for countries
-rw-r--r-- 1 root root   89476 Mar  2 18:55 jquery.min.js             # local version of jquery (however, we use cloud)
-rw-r--r-- 1 root root     778 Mar  2 18:55 pace-big-counter.css      # css style for pace progress bar (we use this)
-rw-r--r-- 1 root root   12736 Mar  2 18:55 pace.min.js               # local version of pace.js (however, we use cloud)
-rw-r--r-- 1 root root 3478132 Mar  2 18:55 plotly-latest.min.js      # local version of plotly (however, we use cloud)

~~~./usa-ca:~~~
-rw-r--r-- 1 root root 12833 Mar  2 17:41 county-plot.py         # main code - plots california counties and creates html output
-rw-r--r-- 1 root root  1069 Feb 24 16:18 county-pop.csv         # csv showing each counties population (called by county-plot.py)

-rw-r--r-- 1 root root 6169982 Mar  2 18:07 county-output.html   # html output of county-plot.pt
-rw-r--r-- 1 root root  649588 Feb 24 16:51 run-$DATE.out  # saved log output of county-plot.py created by ../run.sh
```

## Errors

Possible errors that might be seen:

### Missing _bz2 On Linux

If you get an error during running `usa-ca/county-plot.py` which talks about missing _bz2 module. Then you will need install a linux package and compile python again & you will need to reinstall the python modules with pip.

* Error notes: https://stackoverflow.com/questions/12806122/missing-python-bz2-module
* Compiling new python: https://linuxize.com/post/how-to-install-python-3-9-on-debian-10/

### Other Errors

Might need to google your way around or contact me via "Issues" tab

## To Do

* added population info to country and create new plot html or add subplot with per 100K
