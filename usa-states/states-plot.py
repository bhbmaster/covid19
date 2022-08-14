import pandas as pd
import numpy as np
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import covid_init_and_plot, pd_quick_info_maybe_save # local module but up one directory hence the sys path append ..

###########################################################

### presetting pandas for correct stdout output ###

pd.set_option("max_colwidth", None)
# pd.set_option("max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

# prework
print("------------ preparing dataset -----------")
print()

### constants ###

SHOW_TOP_NUMBER = 6 # 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
csv_file = "us-states.csv"
csv_file_parsable = "us-states-parsable.csv"
filename_prefix = "states"
plot_title = "US States"

# states population file values from 2019 good enough
file_pop = "states-pop.csv"
cpops = pd.read_csv(file_pop,index_col="Rank", skiprows=[1])  # we add skiprows=[1] to skip row 1 which is the USA one (sidenote row 0 is column names)

# covid data
url_data = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"

print("* downloading data 1/1")
c = pd.read_csv(url_data)
print("* downloading data complete")
print()

# analyze and parse population
cpops_state_list = cpops["State"].values.tolist()
cpops_pop_list = cpops["Population"].values.tolist()
cpop_zip = zip(cpops_state_list,cpops_pop_list)
cpop_list = list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet - now we have cpop_list=[('Alabama', 4903185), ('Alaska', 731545), ... ]

# get top 10 (or top SHOW_TOP_NUMBER)
top10 = cpops.head(SHOW_TOP_NUMBER)["State"]
visible_states = top10.values.tolist()

print(f"PARSING population:")
print(f"* {cpop_list=}")
print(f"* {visible_states=}")
print()

# analyze covid data
pd_quick_info_maybe_save(c, "RECEIVED DATA", csv_file)
c_original=c

# goal is to get to look like this:
# date, area, newcountconfirmed*,  totalcountconfirmed,  newcountdeaths*,  totalcountdeaths (we need to calc *)

# remove fips column
cols_to_select = ["date","state","cases","deaths"]
c0 = c[cols_to_select]
c0s = c0.sort_values(by=['date'])

# find all the unique states
unique_states = list(set(c["state"].values.tolist()))  # take a list and convert to set. sets can only have one of the same value. then back to list so we can sort with below func.
unique_states.sort() # alphabetical
print(f"* covid data -> {unique_states=} length {len(unique_states)}")
cpops_state_list_sorted = cpops_state_list
cpops_state_list_sorted.sort()
print(f"* population -> {cpops_state_list_sorted=} length {len(cpops_state_list_sorted)}")
print(f"* Do we get the same areas from Covid Data and Population data: {cpops_state_list_sorted==unique_states}")

# create the new parsable dataframe c1, first start with empty one. we look at every state one by one (they are sorted) from the original dataframe.
# creating a new dataframe from each state (note it just has the cols we want ["date","state","cases","deaths"] and its date sorted)
# we subtract previous rows to create new cols: newcases and newdeaths in this new state dataframe
# then we append this new state dataframe to our new parsable dataframe c1
c1 = pd.DataFrame(columns = ["date","state","cases","newcases","deaths","newdeaths"])
for i,current_state in enumerate(unique_states):
	# print("*", i,current_state)
	cpart = c0s[c0s["state"]==current_state] # select one state
	cpart = cpart.set_index('date') # can index on date and it works too
	cpart["newcases"] = cpart["cases"] - cpart["cases"].shift(1)     # do the diff math for cases
	cpart["newdeaths"] = cpart["deaths"] - cpart["deaths"].shift(1)  # do the diff math for deaths
	cpart = cpart.reset_index() # remove the index so it looks nice (optional as it gets appended)
	# print(cpart.tail())
	c1=c1.append(cpart, ignore_index = True)

# show results of final data frame before plotting
print()
pd_quick_info_maybe_save(c1, "FINAL DATA", csv_file_parsable)

#################################################
#                     PLOT                      #
#################################################

# plot
covid_init_and_plot(c1,cpop_list,filename_prefix,plot_title,[ "date", "state", "cases", "deaths", "newcases", "newdeaths" ],visible_states,to_get_to_root="..",DEBUGAREA="")

##### END #####