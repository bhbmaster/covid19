import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots
from os import path
import plotly.express as px # for themes/templates
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import avgN, human_number, lastXdayslinearpredict  # local module but up one directory hence the sys path append ..

# TODO: #
# read in csv & save it (DONE)
# get population (DONE)
# parse population (DONE)
# split it by state
# sort by date
# do this to create dC and dD https://stackoverflow.com/questions/23142967/adding-a-column-thats-result-of-difference-in-consecutive-rows-in-pandas
# then recombine to new pandas & save new
# plot every state by raw numbers
# plot every state by PER 100K
# do linear regression

# prework
print("------------ initializing -----------")
print()

# constants

VersionFile = "../VERSION"  # Last Update YY.MM.DD
ndays = 7 # how many days is the moving average averaging
output_html = "states-output.html" # relative per population per 100K - THIS IS ORIGINAL PLOT
output_html_1 = "states-output-raw.html" # just raw results (Added later so its output_html_1) - THIS IS NEW PLOT
PER = 100000 # we should per 100000 aka 100K
PER_TEXT = "100K"
SHOW_TOP_NUMBER = 6 # 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
ThemeFile = "../PLOTLY_THEME" # contents are comma sep: theme,font family,font size
predictdays = 30
COLOR_LIST = px.colors.qualitative.Vivid # this sets the colorway option in layout
COLOR_LIST_LEN = len(COLOR_LIST) # we will use the mod of this later
updatedate_dt = datetime.datetime.now()
updatedate_str = updatedate_dt.strftime("%Y-%m-%d %H:%M:%S")
csv_file = "us-states.csv"
csv_file_parsable = "us-states-parsable.csv"

# Get Version
Version = open(VersionFile,"r").readline().rstrip().lstrip() if path.exists(VersionFile) else "NA"

# Get Theme
ThemeFileContents = open(ThemeFile,"r").readline().rstrip().lstrip().split(",")
Theme_Template = ThemeFileContents[0] if path.exists(ThemeFile) else "none"
Theme_Font = ThemeFileContents[1] if path.exists(ThemeFile) else "Arial"
Theme_FontSize = int(ThemeFileContents[2]) if path.exists(ThemeFile) else 12

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
print(f"{unique_states=}")

# --- getting the data of population and downloaded data to equal up - BELOW --- #
# TODO: at this point unique_states and states have some differences we need to find that out and make sure the data is in both
# print()
# print("--- TESTING ---")
# print(f"{len(unique_states)=} {unique_states=}")
# for i in unique_states:
# 	print(i)
# cpop_list_area_names = [ i[0] for i in cpop_list ]
# print(f"{len(cpop_list_area_names)=} {cpop_list_area_names=}")
# for i in cpop_list_area_names:
# 	print(i)
# print()
##################################
# len(unique_states)=55 unique_states=['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Guam', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Northern Mariana Islands', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Puerto Rico', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virgin Islands', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming']
##################################
# len(cpop_list_area_names)=52 cpop_list_area_names=['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'DC', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'USA', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming']
# then printed vertically and ran comm to see differences
# noticed some of the islands and terretories are missing in population list, so i added them manually
# now we have extra entry in population list USA but we dont have data for it here, but we have it else where so lets just remove it for now manually
# once we remove USA from either CSV (nah) or after we read in the CSV (yes) - we did this by skipping row 1
# using cpops = pd.read_csv(file_pop,index_col="Rank", skiprows=[1])
# instead of cpops = pd.read_csv(file_pop,index_col="Rank")
# --- getting the data of population and downloaded data to equal up - ABOVE --- #

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
#################################################

# * graph
# providing "fig" and "fig_1" to plot on. the dataframe to use as "c".
# "area" is the name of the state/county or area, "pop" is the population in that area
# the names of the columns:
# nX = name of the date column (which is our X values)
# nA = name of area column
# nC = name of cases column
# nD = name of deaths column
# nNC = name of new cases column
# nND = name of new deaths column
# "visible_area" = list of areas to show
# "color_index" = if originally set to None then we alternate colors for every trace. if originally we set to -1 here then we match color of prediction
def graph(fig, fig_1, area, pop, c, nX, nA, nC, nD, nNC, nND, visible_areas, color_index):
    # global color_index
    print(f"- {area} pop={pop} - last recorded values below:")
    visible1 = "legendonly" if not area in visible_areas else None
    x=c[c[nA] == area]["date"].values  # same x for relative and normal plot
    # print(f"DEBUG: {x=}")
    FRONTSPACE="    "
    color_text=""
    # note where you see _1 thats for normal plot example: y is for relative original plot and y_1 is for new normal plot

    #####################################################
    # -- newcountconfirmed per 100K (moving average) -- #
    #####################################################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c[nA] == area][nNC].values
    y=orgy/pop*PER  # relative plot
    y_1=orgy        # normal plot
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())          # relative plot average
    avgx_1,avgy_1=avgN(ndays,x.tolist(),y_1.tolist())    # normal plot average
    LastNewC = avgy[-1]
    LastNewC_1 = avgy_1[-1]
    print(f"{FRONTSPACE}NewCases   \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{area}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"
    legendtext_1=f"<b>{area}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy_1[-1]:0.2f}</b>"
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=area,visible=visible1),row=1,col=1)
    fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1),row=1,col=1)
    used_colors_index = color_index # saving current color used (it follows thru the index of the colorway)

    #########################
    # linear regresion line #
    #########################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"

    # we use this code bit twice, so might as well make inner function and it only makes sense in graphing so yup here it will lie as an inner function
    def plot_regression(figure,X,Y,extralabel=""):
        # for any plot
        (success,xfinal,yfinal,r_sq,m,b0) = lastXdayslinearpredict(X,Y,predictdays) # predict days is from global
        # print(f"DEBUG PR ({extralabel}): {success=},{xfinal=},{yfinal=},{r_sq=},{m=},{b0=}")
        # if success:
        entered_prediction_if_loop = False # was used when dates were backwards and m was 0 so we didnt get prediction lines but got the other lines, however, i realized that even after we sorted the dates and it all worked out... what if we get a flat slope m=0 then issue could still happen, so i put this boolean in just in case
        if success and m != 0:
            entered_prediction_if_loop = True
            # y = mx + b ---> (y-b)/m = 0
            y_to_cross = 0
            x_cross1 = (y_to_cross - float(b0)) / float(m)
            x_cross1_int=int(x_cross1)
            day0=xfinal[0]
            day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")
            daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))
            daycross = daycrossdt.strftime("%Y-%m-%d")
            print(f"{FRONTSPACE}- predicted cross ({extralabel})   \t y = {m:0.4f}x+{b0:0.2f} \t r^2={r_sq:0.4f} \t {daycross=}{color_text}")
            # plot
            # legendtext=f"<b>{area}</b> - predict 0 daily cases @ <b>{daycross}</b> by {predictdays}-day linear fit"
            legendtext=f"> PREDICT no new cases in <b>{area}</b> on <b>{daycross}</b>"
            if color_index == None:
                # if color_index is -1 we didn't set it and we will use the default color methods (next color in colorway)
                figure.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(dash='dash')),row=1,col=1)
            else:
                color_index_to_use = used_colors_index % COLOR_LIST_LEN # we circulate thru the color_way so we use modulus
                color_to_use = COLOR_LIST[color_index_to_use] # call that color via index from colorway list
                figure.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use,dash='dash')),row=1,col=1)
        return entered_prediction_if_loop, color_to_use  # return if we successfully predicted (meaning slope isnt 0 and the prediction function returned some good stuff)

    # for relative plot
    entered_prediction_if_loop, color_to_use = plot_regression(fig,avgx,avgy,"relative")
    # for normal plot
    entered_prediction_if_loop_1, color_to_use_1 = plot_regression(fig_1,avgx_1,avgy_1,"normal")
    # - sidenote the result of the relative output should equal same for normal
    # entered_prediction_if_loop, color_to_use should equal entered_prediction_if_loop_1, color_to_use_1

    ##################################################
    # -- newcountdeaths per 100K (moving average) -- #
    ##################################################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c[nA] == area][nND].values
    y=orgy/pop*PER
    y_1=orgy
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    avgx_1,avgy_1=avgN(ndays,x.tolist(),y_1.tolist())
    LastNewD = avgy[-1]
    LastNewD_1 = avgy_1[-1]
    print(f"{FRONTSPACE}NewDeaths      \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{area}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    legendtext_1=f"<b>{area}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    if color_index == None:
        fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=area,visible=visible1),row=2,col=1)
        fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1),row=2,col=1)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use)),row=2,col=1)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use_1)),row=2,col=1)

    ##############################
    # -- total cases per 100K -- #
    ##############################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c[nA] == area][nC].values
    y=orgy/pop*PER
    y_1=orgy
    LastC = y[-1]
    LastC_1 = y_1[-1]
    print(f"{FRONTSPACE}TotalCases \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{area}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    legendtext_1=f"<b>{area}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=area,visible=visible1),row=1,col=2)
        fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1),row=1,col=2)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use)),row=1,col=2)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use_1)),row=1,col=2)

    ###############################
    # -- total deaths per 100K -- #
    ###############################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c[nA] == area][nD].values
    y=orgy/pop*PER
    y_1=orgy
    LastD = y[-1]
    LastD_1 = y_1[-1]
    print(f"{FRONTSPACE}TotalDeaths    \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    # legendtext=f"<b>{area}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    # legendtext_1=f"<b>{area}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    # showing legend at the end as we have all of the Last data
    legendtext = f"<b>{area}</b> ({human_number(pop)}) <b>{LastNewC:0.2f}</b>|{human_number(LastC)}|<b>{LastNewD:0.2f}</b>|{LastD:0.0f}"                 # trying to show every last value
    legendtext_1 = f"<b>{area}</b> ({human_number(pop)}) <b>{LastNewC_1:0.2f}</b>|{human_number(LastC_1)}|<b>{LastNewD_1:0.2f}</b>|{int(LastD_1):,}"       # trying to show every last value
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=True,legendgroup=area,visible=visible1),row=2,col=2)
        fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=True,legendgroup=area,visible=visible1),row=2,col=2)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=True,legendgroup=area,visible=visible1,line=dict(color=color_to_use)),row=2,col=2)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=True,legendgroup=area,visible=visible1,line=dict(color=color_to_use_1)),row=2,col=2)

    # return the altered plotly figures which now have all of the plots & also we return the color_index as we keep track of it for next plot
    return fig, fig_1, color_index

#################################################
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
	fig, fig_1, color_index = graph(**graph_options)
	print()

# fig, fig_1, color_index = graph(*graph_options)

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