import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots
import numpy as np
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import avgN, human_number, lastXdayslinearpredict, graph4area, PER, PER_TEXT, ndays, predictdays, COLOR_LIST, GetVersion, GetTheme  # local module but up one directory hence the sys path append ..

###########################################################

### presettings ###

pd.set_option("max_colwidth", None)
pd.set_option("max_columns", None)

#### init #####

print("------------ initializing -----------")
print()

# dataset site: https://github.com/ccodwg/Covid19Canada
# link: https://github.com/ccodwg/Covid19Canada/blob/master/timeseries_prov/active_timeseries_prov.csv
# actually getting the date from raw github: https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_prov/active_timeseries_prov.csv

# --- get data and manipulate it into correct form --- #

covid_url='https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_prov/active_timeseries_prov.csv' # github
population_file='canada-pop.csv' # local - got data from wikipedia https://en.wikipedia.org/wiki/Population_of_Canada_by_province_and_territory

# --- output names --- #
covid_csv_rx='canada.csv'
covid_csv_final='canada-parsable.csv'
covid_html_normal='canada-output.html' # relative plots
covid_html_raw='canada-output-raw.html'

# --- other variables --- #

VersionFile = "../VERSION"  # Last Update YY.MM.DD
SHOW_TOP_NUMBER = 6 # 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
ThemeFile = "../PLOTLY_THEME" # contents are comma sep: theme,font family,font size
updatedate_dt = datetime.datetime.now()
updatedate_str = updatedate_dt.strftime("%Y-%m-%d %H:%M:%S")

# Get Version
Version = GetVersion(VersionFile)

# Get Theme
Theme_Template, Theme_Font, Theme_FontSize = GetTheme(ThemeFile)

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

c = pd.read_csv(covid_url)

# analyze covid data
print(f"RECEIVED DATA (saved to {covid_csv_rx}):")
print()
print(f"{c.describe()=}")
print()
print(f"{c.tail()=}")
print()
print(f"{c.columns=}")
print()
c.to_csv(covid_csv_rx) # save it locally
c_original = c

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
converted_to_datetime = pd.to_datetime(extracted_date_active_col) # convert string to datetime (this looks like yyyy-mm-dd when printed but when accessed its 1618963200000000000 so we need to convert to yyyy-mm-dd string using line below)
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
print(f"{c3=}")
c3.to_csv(covid_csv_final)

# copy to final dataframe cf
cf = c3

###########################################################

##### plot #####

print()
print("------------ main work -----------")

print()
print(f"- plotting start (theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize})")
print()

# init plots / both figures
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

random_province = cpops_prov_list[0] # we picked next one from the top
print(f"* {random_province=}")
last_x = cf[cf["area"] == random_province]["date"].values.tolist()[-1]
print(f"* {last_x=} of {random_province=}")
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

# give the figures the options and titles we want
predictnote =  f", <b>Note:</b> Prediction uses {predictdays} day linear fit, appears as black-dashed line."

# init settings for both figures (settings for plots and subplots)
fig.update_layout(title=f"<b>Canada Provinces & Territories Covid19 Stats (Relative to Population Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str} {predictnote}",**plot_options) # main title & theme & hover options & font options unpacked
fig_1.update_layout(title=f"<b>Canada Provinces & Territories Covid19 Stats (Normal / Raw Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str}  {predictnote}",**plot_options) # main title & theme & hover options & font options unpacked

# parse each area/province and generate trace in figure
# * consider each area and trace it on plotly
color_index = -1 # if originally set to None then we alternate colors for every trace. if we set to -1 here then we match color of prediction
for prov,pop in cpop_list:
	graph_options = { "fig": fig,
		"fig_1": fig_1,
		"area": prov,
		"pop": pop,
		"c": cf,
		"nX": "date",
		"nA": "area",
		"nC": "cases",
		"nD": "deaths",
		"nNC": "new_cases",
		"nND": "new_deaths",
		"visible_areas": visible_provinces,
		"color_index": color_index }
	fig, fig_1, color_index = graph4area(**graph_options,DEBUGAREA="BC") # fig is relative, fig_1 is raw values
	print()

# save html
# * plotly generate html output generation
fig.write_html(covid_html_normal,auto_open=False)
fig_1.write_html(covid_html_raw,auto_open=False)

# * html div generation (not used)
div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
div_1 = plotly.offline.offline.plot(fig_1, show_link=False, include_plotlyjs=False, output_type='div')
print(f"* size of type & div of relative plot - type(div)={type(div)} len(div)={len(div)}") # div not used
print(f"* size of type & div of normal plot - type(div_1)={type(div_1)} len(div)={len(div_1)}") # div not used
print()

# the end
print("- plotting end")

##### END #####