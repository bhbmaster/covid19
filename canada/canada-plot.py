import pandas as pd
import numpy as np
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import covid_init_and_plot  # local module but up one directory hence the sys path append ..

###########################################################

### presetting pandas for correct stdout output ###

pd.set_option("max_colwidth", None)
# pd.set_option("max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

#### init #####

print("------------ preparing dataset -----------")
print()

# * old data set lasts until 2022-05-03:
# dataset site: https://github.com/ccodwg/Covid19Canada
# link: https://github.com/ccodwg/Covid19Canada/blob/master/timeseries_prov/active_timeseries_prov.csv
# actually getting the date from raw github: https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_prov/active_timeseries_prov.csv

# TODO * use this new data set, however, it is split between cases + deaths, so we will need to figure out how to combine them
# dataset site: https://github.com/ccodwg/Covid19Canada
# link (cases): https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/cases_pt.csv
# link (deaths): https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/deaths_pt.csv

# --- get data and manipulate it into correct form --- #

covid_url='https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_prov/active_timeseries_prov.csv' # github (TODO: remove when fix canada-plot)
covid_url_cases='https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/cases_pt.csv'
covid_url_deaths='https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/deaths_pt.csv'
population_file='canada-pop.csv' # local - got data from wikipedia https://en.wikipedia.org/wiki/Population_of_Canada_by_province_and_territory

# --- output names --- #
covid_csv_rx='canada.csv' ####### (TODO: remove when fix canada-plot)
covid_csv_rx_cases='canada-cases.csv' ####### new for fixing canada-plot
covid_csv_rx_deaths='canada-deaths.csv' ####### new for fixing canada-plot
covid_csv_final='canada-parsable.csv'
filename_prefix="canada"
plot_title="Canada Provinces & Territories"

# --- other variables --- #

SHOW_TOP_NUMBER = 6 # 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)

##### downloading/accessing and manipulating population dataframe #####

cpops = pd.read_csv(population_file,index_col="Rank", skiprows=[1])  # we add skiprows=[1] to skip row 1 which is the Canada one (sidenote row 0 is column names)
cpops_prov_list = cpops["Province or Territory"].values.tolist()
cpops_pop_list = cpops["Population Est 2021"].values.tolist()
cpop_zip = zip(cpops_prov_list,cpops_pop_list)
cpop_list = list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet - now we have cpop_list=[('Alabama', 4903185), ('Alaska', 731545), ... ]

# get top 10 (or top SHOW_TOP_NUMBER)
top10 = cpops.head(SHOW_TOP_NUMBER)["Province or Territory"]
visible_provinces = top10.values.tolist()

print(f"PARSING population:")
print(f"* {cpop_list=}")
print(f"* {visible_provinces=}")
print()

##### downloading/accessing and manipulating covid dataframe #####

c = pd.read_csv(covid_url) # (TODO: remove when fix canada-plot)
c_cases = pd.read_csv(covid_url_cases) ####### new for fixing canada-plot
c_deaths = pd.read_csv(covid_url_deaths) ####### new for fixing canada-plot

######## notes for fixing canada plot
# how original was received
"""
,province,date_active,cumulative_cases,cumulative_recovered,cumulative_deaths,active_cases,active_cases_change
0,Alberta,25-01-2020,0,0,0,0,0
1,Alberta,26-01-2020,0,0,0,0,0
2,Alberta,27-01-2020,0,0,0,0,0
"""
# how final looks after all manipulations
"""
,date,area,cases,new_cases,deaths,new_deaths
0,2020-01-25,Alberta,0,,0,
1,2020-01-26,Alberta,0,0.0,0,0.0
"""
######## end of notes for fixing canada plot

# analyze covid data
print(f"RECEIVED DATA (saved to {covid_csv_rx}):")
print()
print(f"RX c.describe():\n{c.describe()}")
print()
print(f"RX c.tail():\n{c.tail()}")
print()
print(f"RX c.columns:\n{c.columns}")
print()
c.to_csv(covid_csv_rx) # save it locally
c_original = c

# analyze covid cases data ####### new for fixing canada-plot
print(f"RECEIVED CASES DATA (saved to {covid_csv_rx_cases}):")
print()
print(f"RX c_cases.describe():\n{c_cases.describe()}")
print()
print(f"RX c_cases.tail():\n{c_cases.tail()}")
print()
print(f"RX c_cases.columns:\n{c_cases.columns}")
print()
c_cases.to_csv(covid_csv_rx_cases) # save it locally
c_cases_original = c_cases

# analyze covid deaths data ####### new for fixing canada-plot
print(f"RECEIVED DEATHS DATA (saved to {covid_csv_rx_deaths}):")
print()
print(f"RX c_deaths.describe():\n{c_deaths.describe()}")
print()
print(f"RX c_deaths.tail():\n{c_deaths.tail()}")
print()
print(f"RX c_deaths.columns:\n{c_deaths.columns}")
print()
c_deaths.to_csv(covid_csv_rx_deaths) # save it locally
c_deaths_original = c_deaths

####### canada-plot: *** got to here *** now must analyze output of c_cases & c_deaths & c
#######              above + associated csv files canada{,_cases,_deaths}.csv.
#######              with analysis come up with plan on how to convert
#######              c_cases and c_deaths to look like c or look like c3 or
#######              cf below (which is saved to canada-parsable.csv). if doing the latter
#######              plan of making it look like c3 or cf, might to change more code below.
#######              otherwise, can stop after c.

# renaming cols
rename_dict = {"province": "area", "date_active": "date", "cumulative_cases": "cases", "cumulative_deaths": "deaths"}
cr = c.rename(columns=rename_dict)

# select whats important
cols_to_select = [ "area", "date", "cases", "deaths" ]
c0 = cr[cols_to_select]

# remove "Repatriated" province as we dont have population data for it, and its kind of a useless stat
c1 = c0[c0["area"] != "Repatriated"]

# find all unique provinces and compare with population (they must match)
unique_provinces = list(set(c1["area"].values.tolist()))
unique_provinces.sort()
print(f"* covid data -> {unique_provinces=} , length {len(unique_provinces)}")
cpops_prov_list_sorted = cpops_prov_list
cpops_prov_list_sorted.sort()
print(f"* population -> {cpops_prov_list_sorted=} , length {len(cpops_prov_list_sorted)}")
print(f"* Do we get the same areas from Covid Data and Population data: {cpops_prov_list_sorted==unique_provinces}")

# fix dates from dd-mm-yyyy to yyyy-mm-dd -> extract col, convert to datetime64 then to string, insert new col
extracted_date_active_col = c1['date']
converted_to_datetime = pd.to_datetime(extracted_date_active_col, dayfirst=True) # convert date string string to datetime object. it guesses the date format, so first it might pick mm-dd-yyyy even though its dd-mm-yyyy. we tell it that its canadien format with dayfirst=True. another way is with format='%d-%m-%Y'. this looks like yyyy-mm-dd when printed but when accessed its 1618963200000000000 so we need to convert to yyyy-mm-dd string using line below.
correct_datetime_col = converted_to_datetime.apply(lambda x: x.strftime('%Y-%m-%d')) # this should do it?
c2 = c1 # copy dataframe
c2["date"] = correct_datetime_col # overwrite corrected date col into old date col
print()
print("REMOVED EXTRA COLS AND UNNEEDED 'Repatriated' VALUES & CONVERTED DATE TO yyyy-mm-dd:")
print(f"{c2=}")

# pd.to_datetime line gives us this warning:
# /Users/kostia/Dropbox/src/covid19/canada/canada-plot.py:97: SettingWithCopyWarning:
# A value is trying to be set on a copy of a slice from a DataFrame.
# Try using .loc[row_indexer,col_indexer] = value instead
# See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy

# sort everything now that its correct datetime format (which is sortable)
c2s = c2.sort_values(by=['date'])

# adding column for delta cases and deaths
c3 = pd.DataFrame(columns = ["date","area","cases","new_cases","deaths","new_deaths"])
for i, current_prov in enumerate(unique_provinces):
	print("*", i, current_prov)
	cpart = c2s[c2s["area"]==current_prov] # select one prov
	cpart = cpart.set_index('date') # can index on date and it works too
	cpart["new_cases"] = cpart["cases"] - cpart["cases"].shift(1)     # do the diff math for cases
	cpart["new_deaths"] = cpart["deaths"] - cpart["deaths"].shift(1)  # do the diff math for deaths
	cpart = cpart.reset_index() # remove the index so it looks nice (optional as it gets appended)
	# print(cpart.tail())
	print(f"{c3.tail()}")
	c3 = c3.append(cpart, ignore_index = True)

# print and save
print()
print(f"FINAL PARSABLE DATA (saved to {covid_csv_final}):")
print()
print(f"FINAL c3.describe():\n{c3.describe()}")
print()
print(f"FINAL c3.tail():\n{c3.tail()}")
print()
print(f"FINAL c3.columns:\n{c3.columns}")
c3.to_csv(covid_csv_final)

# copy to final dataframe cf
cf = c3

#################################################
#                     PLOT                      #
#################################################

# plot
covid_init_and_plot(cf,cpop_list,filename_prefix,plot_title,[ "date", "area", "cases", "deaths", "new_cases", "new_deaths" ],visible_provinces,to_get_to_root="..",DEBUGAREA="")

##### END #####