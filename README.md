# covid19plot.py

The public facing version of this project resides on my personal blog, **infotinks.com**:

**http://www.infotinks.com/coronavirus-dashboard-covid19-py/**.

From there all of the plot outputs can be accessed + some other interesting information.

Additionally, the data sources are mentioned in the "Data Sources section" there.

The rest of this Readme covers the following:
* The different outputs that are provided by the different scripts. 
* Requirements to run the scripts.
* How to run the scripts
* Wrapper scripts that are helpful in launching all of the scripts at once. 
* Some notes on running this from VirtualEnv.
* Some notes on all of the files seen in each directory and what they are for.
* Then some final words on some errors and ignorable warnings that might be encoutered.

## Outputs

There are 4 python scripts that generate different outputs:

* (1) `covid19plot.py` - world plots
* (2) `usa-states/states-plot.py` - usa states plots
* (3) `usa-ca/county-plot.py` - california county plots
* (4) `canada/canada-plot.py` - canada provinces and territory plots

Here they are in more detail:

**(1) `covid19plot.py` produces the following graphs:**

- Normal Axes plots of every country to `covid19-normal.html`: **http://www.infotinks.com/covid19/covid19-normal.html**

- Log Axes plots of every country in to `covid19-log.html`: **http://www.infotinks.com/covid19/covid19-log.html**

- Relative to Population Normal Axes plots of every country to `covid19-normal-perpop.html`: **http://www.infotinks.com/covid19/covid19-normal-perpop.html**

- Relative to Population Log Axes plots of every country in to `covid19-log-perpop.html`: **http://www.infotinks.com/covid19/covid19-log-perpop.html**

- Each country generates its own seperate normal and log plot into the `html-plots/` directory. As these are smaller the browser has an easier time allowing interaction with these plots

Example: 

```
html-plots/US-plot-NORMAL.html           - raw values
html-plots/US-plot-LOG.html              - raw values
html-plots/US-plot-NORMAL-perpop.html    - values adjusted by population per 100K people
html-plots/US-plot-LOG-perpop.html       - values adjusted by population per 100K people
```

**(2) `usa-states/states-plot.py` produces the similar graphs and outputs:**

- Daily New Cases in every US state is plotted to `usa-states/states-output.html` and `usa-states/states-output-raw.html`
- Relative per Population Plot: **http://www.infotinks.com/covid19/usa-states/states-output.html**
- Normal Plot: **http://www.infotinks.com/covid19/usa-states/states-output-raw.html**
- `usa-states/states-output.html` shows the values of the States of the USA relative to the population per 100K and with 7 day moving average
- `usa-states/states-output-raw.html` shows the raw values of the States of the USA with 7 day moving average
- The moving average only applies to Daily New Cases & Daily New Deaths plots. The Total Cases & Total Deaths plot do not have the moving average function applied to them
- Also this script saves the raw csv data that was downloaded `usa-states/us-states.csv` and then saves the manipulated dataframe(csv) that is parsed by the graph4area() function to `usa-states/us-states-parsable.csv`

**(3) `usa-ca/county-plot.py` produces the following graphs and outputs:**

- Daily New Cases in all California countys plotted to `usa-ca/county-output.html` and `usa-ca/county-output-raw.html`
- Relative per Population Plot: **http://www.infotinks.com/covid19/usa-ca/county-output.html**
- Normal Plot: **http://www.infotinks.com/covid19/usa-ca/county-output-raw.html**
- `usa-ca/county-output.html` shows the values of the counties and California state relative to the population per 100K and with 7 day moving average
- `usa-ca/county-output-raw.html` shows the raw values of the counties and California state with 7 day moving average
- The moving average only applies to Daily New Cases & Daily New Deaths plots. The Total Cases & Total Deaths plot do not have the moving average function applied to them
- Also this script saves the raw csv data that was downloaded `usa-ca/CA-covid19cases_test.csv` and then saves the manipulated dataframe(csv) that is parsed by the graph() function to `usa-ca/CA-covid19cases_test-parsable.csv`

**(4) `canada/canada-plot.py` produces the similar graphs and outputs:**

- Daily New Cases in every Canada Province & Territory is plotted to `canada/canada-output.html` and `canada/canada-output-raw.html`
- Relative per Population Plot: **http://www.infotinks.com/covid19/canada/canada-output.html**
- Normal Plot: **http://www.infotinks.com/covid19/canada/canada-output-raw.html**
- `canada/canada-output.html` shows the values of the Provinces & Territories of Canada relative to the population per 100K and with 7 day moving average
- `canada/canada-output-raw.html` shows the raw values of the Provinces & Territories of Canada with 7 day moving average
- The moving average only applies to Daily New Cases & Daily New Deaths plots. The Total Cases & Total Deaths plot do not have the moving average function applied to them
- Also this script saves the raw csv data that was downloaded `canada/canada.csv` and then saves the manipulated dataframe(csv) that is parsed by the graph4area() function to `canada/canada-parsable.csv`

## Requirements

* View requirements.txt to see the required python modules

* This is only tested with Python 3.9.0. It should work with anything newer and not older. Why? The new `f"{var=}"` format is introduced in 3.9 and is used in some of the prints

* Internet access (see Other Requirements below)

## Required Python version & how to launch the scripts

### Which python executable to use

As noted we use Python3.9 or newer. Launching the scripts might be different on each system. Therefore minor editing of `run.sh` or the example commands might be necessary for them to work.

Assuming you have python 3.9 installed correct, launching the scripts should work using one of these methods:

```bash
python script.py
python3 script.py
python3.9 script.py
```

Tip: You can find out which one will work before hand by running `python -V`, `python3 -V` or `python3.9 -V`. Which ever returns python 3.9 or greated is the version you shall use on that system. Similar care must be taken when installing the required modules.

### Current working directory

Additionally, care must be taken of the current working directory. This is because all of the required files that the script might need are referenced from their directory. Additionally, all of the outputs go into the directory where the script lies.

In otherwords, make sure you `cd` into the directory where each script lies.

Example 1: For the world plots which lie on the root directory of the project, cd to the root directory of the project.
```bash
cd /.../covid19/
python covid19plot.py
```

Example 2: For the USA state plots which lie in the usa-state directory in the project, cd to that directory and then run the pthon script. Since this is a subdirectory its generally good to follow up with cd .. so we return to the root. 

```bash
cd /.../covid19/usa-states/
python states-plot.py
cd ..
```

## Required Python Module

The required python modules can be installed using pip.

* Install all modules like so:

```bash
pip install -r requirements.txt
```

Or install the modules listed in `requirements.txt` one by one using `pip install <module>`

## Other Requirements

* Internet access to access the data sources

## Wrapper run.sh Script & places.sh

The wrapper script `run.sh` execute `covid19plot.py` which generates both of the html files to same directory - while also logging any terminal output to a log file, `run-$DATE.out` (this output is used by a log parser tool I call places.sh). It also runs `usa-ca/county-plot.py` which generates `usa-ca/county-output.html` and redirects its logout to `usa-ca/run-$DATE.out`

Then my `places.sh` uses those log files to get ordered list of most cases for each day. For any given date, one can see which country ranks amongst highest cases. The output is saved in this html file:

- Places output: **http://www.infotinks.com/covid19/places.html**

*Sidenote:* The version of python is specified with the `PYTHON` variable at the beginning of the run.sh script. This is important for my linux server because the `python` program points to `python2.7` by default, so I must specify python 3 by using the `python3.x` program call (such as `python3.9`)

*Sidenote:* Created two wrapper scripts for `run.sh`, `run-wrapper.sh` & `run-and-pull-wrapper.sh`. One just kicks off `run.sh`, prints the PIDS, and follows the log. The latter updates the latest code from git using `git pull` and then kicks off `run.sh`, prints the PIDS and follows the log. Canceling the log follow, doesn't cancel the operation - you will need to kill the posted PIDs.

## Simple Wrapper Script

Run `run-simple-mac.sh` from root directory of the project and it will run `usa-ca/county-plot.py` and then `covid19plot.py`. Output is shown on terminal and not saved to run logs for parsing. This runs the faster script first, unlike the `run.sh` wrapper script which runs the lengthier plotter (covid19plot.py) first.

From a MAC run `run-simple-open-mac.sh` which runs the same two scripts and then opens the results in a default browser. This will work on MAC but probably not Windows or Linux as it uses `open <file>` program (if I am not mistaken that is only supported on MACs; for other OS need different program to launch files with their default application).

*Sidenote:* These scripts call the default python program using python. So if that calls `python2.7` for you, this script will fail. To fix that, you will need to edit the script to call `python3.x`, such as `python3.9`, instead just `python`.

## Execute Program - Running The Program - Generating The Output Data

Just run `covid19plot.py` with `python3.9` or newer, that will gather data, parse it and generate directory html_plots/ and dump 2 graphs for each country (normal y axes and log y axes) in dir. As Total worldwide cases/recovery/deaths is not provided in the json time series, the script manually calculates from the data for each day by summing through all of the countries. It will provide both plots for TOTAL in the same dir as well. It then creates covid19-log.html and covid19-normal.html in the root directory for all of the countries, TOTAL at the top, then sorted by number of cases.

If you want to run this on a schedule, I recommend running it after midnight each day as the timeseries data updates once a day. On my infotinks site it runs 4 times a day 00:05, 06:05, 12:05, 18:05 using crontab. It executes `run.sh` which runs `covid19plot.sh` and saves the output to `run-$DATE.out` and then it run `places.sh` (to generate the extra places document). All of this generates the output files `covid19-log.html`, `covid19-normal.html` and `places.html` which are linked to from my infotinks site. It then runs all of the python plot files for Canada, USA States, and California counties.

My crontab is setup to kick off everything from `run.sh` like this:

```
# env vars for processes - we have to specify PATH and one of those should include where your python3.9 process is
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SHELL=/bin/bash

# m h  dom mon dow   command
5 0,6,12,18 * * * /var/www/covid19/run.sh
```


Instead of running `run.sh`, you can manually run each script like so (python = python3.9 or newer):

```bash
python covid19plot.py                           # main world plotted
cd usa-states; python states-plots.py; cd ..    # plot usa states
cd usa-ca; python county-plot.py; cd ..         # plot california counties
cd canada; python canada-plot.py; cd ..         # plot canada provinces
```

When running run.sh you can kick it off into the background so that you can follow the output log it creates. (sidenote these logfiles on the root of covid19 dir are the ones processed by places.sh)

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
To run `covid19ploy.py` and `usa-ca/county-plot.py` and `usa-states/us-states.csv` please kick off any of the following

```
python3 covid19plot.py
cd usa-states; python3 states-plots.py; cd ..
cd usa-ca; python3 county-plot.py; cd ..
cd canada; python3 canada-plot.py; cd ..
```

or:

```
./run.sh                      # runs all 3 and logs to run*out file in scripts directory - this is what I call in crontab
```

or:

```
./run-wrapper.sh              # this runs run.sh but shows its PID and follows the log for you
```

or to update to latest version (git pull) and then run:

```
./run-and-pull-wrapper.sh     # this runs git pull to get latest version and shows its PID and follows the log for you
```

## File Structure

Here are the dirs and files

```bash
covid19plot# ls --hide "run*" --hide "*html" -R -l

~~~.:~~~
-rwxr-xr-x 1 root root 42888 Mar  2 18:55 covid19plot.py          # main code - plots countrys and creates html output
-rw-r--r-- 1 root root 3660 Jun  8 04:37 world-pop.csv            # every countries population
-rw-r--r-- 1 root root 26049 Apr  1 18:20 common.py               # common code between all of the scripts
-rw-r--r-- 1 root root 27340556 Mar  2 18:07 covid19-log.html     # log plots of country covid stats
-rw-r--r-- 1 root root 27338240 Mar  2 18:07 covid19-normal.html  # normal plots of country covid stats
-rw-r--r-- 1 root root 27340556 Mar  2 18:07 covid19-log-perpop.html     # relative to population log plots of country covid stats
-rw-r--r-- 1 root root 27338240 Mar  2 18:07 covid19-normal-perpop.html  # relative to population normal plots of country covid stats
-rw-r--r-- 1 root root  7189726 Mar  2 18:07 places.html          # ranking countries from highest to lowest cases each day

-rw-r--r-- 1 root root   646 Mar  2 00:35 PLOTLY_THEME          # theme file
-rw-r--r-- 1 root root  6155 Mar  1 22:10 README.md             # this readme
-rw-r--r-- 1 root root     9 Mar  2 10:26 VERSION               # version
-rwxr-xr-x 1 root root  1364 Feb 25 16:30 places.sh             # parses output files generated from run.sh & generates places.html 
-rw-r--r-- 1 root root    44 Feb 24 16:47 requirements.txt      # python requirements

-rwxr-xr-x 1 root root     1709 Mar  1 22:10 run.sh             # for infotinks server - covid19plot.py and county-plot.py, creates run-$DATE-out log files, and runs place.sh (crontab calls this)
-rwxr-xr-x 1 root root      814 Mar  1 22:14 run-and-pull-wrapper.sh     # for infotinks server - sync code from git and kick off run.sh into background and follow log
-rwxr-xr-x 1 root root      688 Mar  1 22:14 run-wrapper.sh              # for infotinks server - kick off run.sh into background and follow log
-rw-r--r-- 1 root root    22166 Mar  2 10:28 run-$DATE.out               # several of these exist, output from run.sh parsed by places.sh


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

~~~./usa-states:~~~
-rw-r--r-- 1 root root    9544 Apr  1 18:20 states-plot.py           # main code - plots usa-states counties and creates html output
-rw-r--r-- 1 root root    1508 Mar 31 23:31 states-pop.csv           # population csv of every state and territory
-rw-r--r-- 1 root root 1034072 Apr  5 12:07 us-states-parsable.csv   # the final modified dataframe is saved as csv and fed to plotter covid_init_and_plot() -> graph4area()
-rw-r--r-- 1 root root  868077 Apr  5 12:07 us-states.csv            # output csv file as downloaded by source
-rw-r--r-- 1 root root 6169982 Apr  2 18:07 county-output.html       # html output of county-plot.py
-rw-r--r-- 1 root root 6169982 Apr  2 18:07 county-output-raw.html   # html output of county-plot.py
-rw-r--r-- 1 root root  649588 Feb 24 16:51 run-$DATE.out            # saved log output of county-plot.py created by ../run.sh

~~~./usa-ca:~~~
-rw-r--r-- 1 root root 12833 Mar  2 17:41 county-plot.py         # main code - plots california counties and creates html output
-rw-r--r-- 1 root root  1069 Feb 24 16:18 county-pop.csv         # csv showing each counties population (called by county-plot.py)
-rw-r--r-- 1 root root 1237742 Apr  2 06:07 CA-covid19cases_test-parsable.csv  # the final modified dataframe is saved as csv and fed to plotter covid_init_and_plot() -> graph4area()
-rw-r--r-- 1 root root 3192794 Apr  2 06:07 CA-covid19cases_test.csv           # output csv file as downloaded from source
-rw-r--r-- 1 root root 6169982 Mar  2 18:07 county-output.html           # html output of county-plot.py
-rw-r--r-- 1 root root 6169982 Mar  2 18:07 county-output-raw.html       # html output of county-plot.py
-rw-r--r-- 1 root root  649588 Feb 24 16:51 run-$DATE.out                # saved log output of county-plot.py created by ../run.sh

~~~./canada:~~~
-rw-r--r-- 1 root root  11032 Apr 22 01:58 canada-plot.py            # main code - plot canada provinces & territories
-rw-r--r-- 1 root root 231660 Apr 22 01:44 canada-parsable.csv       # the final modified dataframe is saved as csv and fed to plotter covid_init_and_plot() -> graph4area()
-rw-r--r-- 1 root root    289 Apr 21 22:24 canada-pop.csv            # canada population data
-rw-r--r-- 1 root root 258025 Apr 22 01:44 canada.csv                # the data source
-rw-r--r-- 1 root root 300000 Apr 22 18:07 canada-output.html        # html output of canada-plot.py
-rw-r--r-- 1 root root 300000 Apr 22 18:07 canada-output-raw.html    # html output of canada-plot.py
-rw-r--r-- 1 root root  64988 Apr 22 16:51 run-$DATE.out             # saved log output of county-plot.py created by ../run.sh
```

## Errors

Possible halting errors that might need to be addressed if encountered.

### Missing *_bz2* On Linux

If you get an error during running `usa-ca/county-plot.py` which talks about missing *_bz2* module. Then you will need install a linux package and compile python again & you will need to reinstall the python modules with pip.

* Error notes: https://stackoverflow.com/questions/12806122/missing-python-bz2-module
* Compiling new python: https://linuxize.com/post/how-to-install-python-3-9-on-debian-10/

### Other Errors

Might need to google your way around or contact me via "Issues" tab.

## Warnings

Note some messages might just be warnings that can be ignored.

* LZMA Warning in all scripts

This LZMA warning for me can be ignored - I only get on my linux server but not on MAC or Windows. Regardless of this warning, everything still works and generates proper plots.

```bash
covid19plot# python3 [covid19plot.py|usa-ca/county-plot.py|usa-states/states-plot.py|canada/canada-plot.py]
/usr/local/lib/python3.9/site-packages/pandas/compat/__init__.py:97: UserWarning:

Could not import the lzma module. Your installed Python is incomplete. Attempting to use lzma compression will result in a RuntimeError.

...next lines not shown as it continued to work...
```

* Fit Warning in all scripts

Additionally, this message can be ignored. This messages happens a few times when it makes a prediction linear fit. Regardless we still get a fit.

```bash
* WARNING in lastXdayslinearpredict: array must not contain infs or NaNs
```

* Copy Warning in Canada script

This warning appears when we use Pandas to convert the Canadian formatted date column from dd-mm-yyyy to DateTime64 Object. This action generates the warning that can be ignored - perhaps there is another way to do it, without generating the warning, but regardless it all works out so we just ignore it. Sidenote: After converting to Datetime64 object, we convert it to yyyy-mm-dd. You can see this by analyzing canada.csv (which is the original dataset with the Canadian dates dd-mm-yyyy) and then analyzing the canada-parsable.csv (which is the final dataframe that gets read in by the covid_init_and_plot() function)

```bash
covid19plot# python3 canada-plot.py
./covid19/canada/canada-plot.py:98: SettingWithCopyWarning:

A value is trying to be set on a copy of a slice from a DataFrame.
Try using .loc[row_indexer,col_indexer] = value instead

See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
```

## Data Sources

The data sources are mentioned in two areas. So putting it here as well will be redundant.

* First, you can see the data sources on http://www.infotinks.com/coronavirus-dashboard-covid19-py/. Scroll down to "Data Sources". 

* Second, The world covid plots also list the data sources for all of the plots. These are at the bottom of the notes section, which comes before all of the country plots. The world covid plots can be viewed from two links (y-log or y-normal plot): 
	* y-log plot: http://www.infotinks.com/covid19/covid19-log.html
	* y-normal plot: http://www.infotinks.com/covid19/covid19-normal.html

## To Do

[x] Add population info to country and create new plot html or add subplot with per 100K

[ ] Add new graph called Deaths Per Cases
