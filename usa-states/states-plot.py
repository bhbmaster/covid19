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

# constants

VersionFile = "../VERSION"  # Last Update YY.MM.DD
ndays = 7 # how many days is the moving average averaging
output_html = "states-output.html" # relative per population per 100K - THIS IS ORIGINAL PLOT
output_html_1 = "states-output-raw.html" # just raw results (Added later so its output_html_1) - THIS IS NEW PLOT
PER = 100000 # we should per 100000 aka 100K
PER_TEXT = "100K"
SHOW_TOP_NUMBER = 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
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
cpops = pd.read_csv(file_pop,index_col="Rank")

# covid data
url_data = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
c = pd.read_csv(url_data)

# analyze and parse population
cpops_state_list=cpops["State"].values.tolist()
cpops_pop_list=cpops["Population"].values.tolist()
cpop_zip=zip(cpops_state_list,cpops_pop_list)
cpop_list=list(cpop_zip)
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
print(c.describe())
print(c.head())
c.to_csv(csv_file) # save it locally

