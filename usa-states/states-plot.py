import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots
import numpy as np
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import avgN, human_number, lastXdayslinearpredict, graph4area, PER, PER_TEXT, ndays, predictdays, COLOR_LIST, GetVersion, GetTheme  # local module but up one directory hence the sys path append ..

### presettings ###

pd.set_option("max_colwidth", None)
pd.set_option("max_columns", None)

# prework
print("------------ initializing -----------")
print()

### constants ###

VersionFile = "../VERSION"  # Last Update YY.MM.DD
output_html = "states-output.html" # relative per population per 100K - THIS IS ORIGINAL PLOT
output_html_1 = "states-output-raw.html" # just raw results (Added later so its output_html_1) - THIS IS NEW PLOT
SHOW_TOP_NUMBER = 6 # 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
ThemeFile = "../PLOTLY_THEME" # contents are comma sep: theme,font family,font size
updatedate_dt = datetime.datetime.now()
updatedate_str = updatedate_dt.strftime("%Y-%m-%d %H:%M:%S")
csv_file = "us-states.csv"
csv_file_parsable = "us-states-parsable.csv"

# Get Version
Version = GetVersion(VersionFile)

# Get Theme
Theme_Template, Theme_Font, Theme_FontSize = GetTheme(ThemeFile)

# states population file values from 2019 good enough
file_pop = "states-pop.csv"
cpops = pd.read_csv(file_pop,index_col="Rank", skiprows=[1])  # we add skiprows=[1] to skip row 1 which is the USA one (sidenote row 0 is column names)

# covid data
url_data = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
c = pd.read_csv(url_data)

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
print(f"RECEIVED DATA (saved to {csv_file}):")
print()
print(f"{c.describe()=}")
print()
print(f"{c.tail()=}")
print()
print(f"{c.columns=}")
print()
c.to_csv(csv_file) # save it locally
c_original=c

# goal is to get to look like this:
# date, area, newcountconfirmed*,  totalcountconfirmed,  newcountdeaths*,  totalcountdeaths (we need to calc *)

# remove fips column
cols_to_select = ["date","state","cases","deaths"]
c0 = c[cols_to_select]
c0.sort_values(by=['date'])

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
	cpart = c0[c0["state"]==current_state] # select one state
	cpart = cpart.set_index('date') # can index on date and it works too
	cpart["newcases"] = cpart["cases"] - cpart["cases"].shift(1)     # do the diff math for cases
	cpart["newdeaths"] = cpart["deaths"] - cpart["deaths"].shift(1)  # do the diff math for deaths
	cpart = cpart.reset_index() # remove the index so it looks nice (optional as it gets appended)
	# print(cpart.tail())
	c1=c1.append(cpart, ignore_index = True)

print()
print(f"FINAL PARSABLE DATA (saved to {csv_file_parsable}):")
print(f"{c1=}")
c1.to_csv(csv_file_parsable)

# at this point lets call it cf (cfinal) and thats what we will use for plotting
cf = c1

# what we have at this point:
#              date    state  cases  newcases deaths  newdeaths
# 0      2020-03-13  Alabama      6       NaN      0        NaN
# 1      2020-03-14  Alabama     12       6.0      0        0.0
# 2      2020-03-15  Alabama     23      11.0      0        0.0
# 3      2020-03-16  Alabama     29       6.0      0        0.0
# 4      2020-03-17  Alabama     39      10.0      0        0.0
# ...
# 21624  2021-03-26  Wyoming  56046     126.0    695        0.0
# 21625  2021-03-27  Wyoming  56046       0.0    695        0.0
# 21626  2021-03-28  Wyoming  56046       0.0    695        0.0
# 21627  2021-03-29  Wyoming  56190     144.0    695        0.0
# 21628  2021-03-30  Wyoming  56236      46.0    695        0.0
# [21629 rows x 6 columns]

#################################################
#                     PLOT                      #
#################################################

print()
print("------------ main work -----------")

print()
print(f"- plotting start (theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize})")
print()

# get titles
subplot_titles = (f"<b>Daily New Cases per {PER_TEXT} {ndays}-day Moving Average</b>",
                  f"<b>Total Cases per {PER_TEXT}</b>",
                  f"<b>Daily New Deaths per {PER_TEXT} {ndays}-day Moving Average</b>",
                  f"<b>Total Deaths per {PER_TEXT}</b>")
subplot_titles_1 = (f"<b>Daily New Cases {ndays}-day Moving Average</b>",
                  f"<b>Total Cases</b>",
                  f"<b>Daily New Deaths {ndays}-day Moving Average</b>",
                  f"<b>Total Deaths</b>")

# spacings for subplots
bigportion = 0.618 # ratio of screen space for left plots
smallportion = 1-bigportion
spacing=0.05

# init plotly figures and their subplots
# subplots
fig = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all
fig_1 = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles_1, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all

random_state = cpops_state_list[1] # we picked next one from the top USA not in list
print(f"* {random_state=}")
last_x = cf[cf["state"] == random_state]["date"].values.tolist()[-1]
print(f"* {last_x=} of {random_state=}")
print()

# plot options
# supported fonts: https://plotly.com/python/reference/layout/
plot_options={
    "hoverlabel_font_size": Theme_FontSize,
    "title_font_size": Theme_FontSize+2,
    "legend_font_size": Theme_FontSize-1,
    "legend_title_font_size": Theme_FontSize+1,
    "font_size": Theme_FontSize,
    "hoverlabel_font_family": Theme_Font,
    "title_font_family": Theme_Font,
    "legend_font_family": Theme_Font,
    "font_family": Theme_Font,
    "hoverlabel_namelength": -1,  # the full line instead of the default 15
    "hovermode": 'x',
    "template": Theme_Template,
    "colorway": COLOR_LIST,
    "legend_title_text": "<b>* Legend Format:</b><br><b>Area</b> (Pop) <b>NewC</b>|TotalC|<b>NewD</b>|TotalD<br><b>* Note1:</b> Latest values are presented<br><b>* Note2:</b> K=1,000 and M=1,000,000<br>----------------------------------------------"
}

## --- ##

# give the figures the options and titles we want
predictnote =  f", <b>Note:</b> Prediction uses {predictdays} day linear fit, appears as black-dashed line."
fig.update_layout(title=f"<b>US States Covid19 Stats (Relative to Population Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str} {predictnote}",**plot_options) # main title & theme & hover options & font options unpacked
fig_1.update_layout(title=f"<b>US States Covid19 Stats (Normal / Raw Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str}  {predictnote}",**plot_options) # main title & theme & hover options & font options unpacked

# * consider each county and trace it on plotly
color_index = -1 # if originally set to None then we alternate colors for every trace. if we set to -1 here then we match color of prediction
for state,pop in cpop_list:
	graph_options = { "fig": fig,
		"fig_1": fig_1,
		"area": state,
		"pop": pop,
		"c": cf,
		"nX": "date",
		"nA": "state",
		"nC": "cases",
		"nD": "deaths",
		"nNC": "newcases",
		"nND": "newdeaths",
		"visible_areas": visible_states,
		"color_index": color_index }
	fig, fig_1, color_index = graph4area(**graph_options)
	print()

# fig, fig_1, color_index = graph4area(*graph_options)

# * plotly generate html output generation
fig.write_html(output_html,auto_open=False)
fig_1.write_html(output_html_1,auto_open=False)

# * html div generation (not used)
div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
div_1 = plotly.offline.offline.plot(fig_1, show_link=False, include_plotlyjs=False, output_type='div')
print(f"* size of type & div of relative plot - type(div)={type(div)} len(div)={len(div)}") # div not used
print(f"* size of type & div of normal plot - type(div_1)={type(div_1)} len(div)={len(div_1)}") # div not used
print()

# the end
print("- plotting end")

### END