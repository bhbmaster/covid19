import pandas as pd
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import (  # local module but up one directory hence the sys path append ..
    covid_init_and_plot,
    pd_quick_info_maybe_save,
    pandas_display_options,
    read_csv_from_url,
    add_daily_diffs,
    NYT_US_STATES_CSV,
    NYT_COVID_REPO,
)

###########################################################

### presetting pandas for correct stdout output ###

pandas_display_options()
# pd.set_option("display.max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

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

# covid data: NY Times full historical state archive (2020-01-21 through 2023-03-23)
# https://github.com/nytimes/covid-19-data
url_data = NYT_US_STATES_CSV

print(f"* downloading US states historical data from {NYT_COVID_REPO}")
c = read_csv_from_url(url_data)
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

# keep the historical cumulative columns and compute daily diffs for every state
cols_to_select = ["date","state","cases","deaths"]
c0 = c[cols_to_select].copy()
c0["date"] = pd.to_datetime(c0["date"], errors="coerce")
c0 = c0.dropna(subset=["date", "state"])
c0["date"] = c0["date"].dt.strftime("%Y-%m-%d")
c0["cases"] = pd.to_numeric(c0["cases"], errors="coerce").fillna(0)
c0["deaths"] = pd.to_numeric(c0["deaths"], errors="coerce").fillna(0)
c1 = add_daily_diffs(c0, "state", "date", "cases", "deaths")

# find all the unique states
unique_states = sorted(c1["state"].unique().tolist())
print(f"* covid data -> {unique_states=} length {len(unique_states)}")
cpops_state_list_sorted = sorted(cpops_state_list)
print(f"* population -> {cpops_state_list_sorted=} length {len(cpops_state_list_sorted)}")
print(f"* Do we get the same areas from Covid Data and Population data: {cpops_state_list_sorted==unique_states}")
print(f"* date range: {c1['date'].min()} through {c1['date'].max()}")

# show results of final data frame before plotting
print()
pd_quick_info_maybe_save(c1, "FINAL DATA", csv_file_parsable)

#################################################
#                     PLOT                      #
#################################################

# plot
covid_init_and_plot(c1,cpop_list,filename_prefix,plot_title,[ "date", "state", "cases", "deaths", "newcases", "newdeaths" ],visible_states,to_get_to_root="..",DEBUGAREA="")

##### END #####
