import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots
import plotly.express as px # for themes/templates
import numpy as np
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import avgN, human_number, lastXdayslinearpredict, graph4area, PER, PER_TEXT, ndays, predictdays, COLOR_LIST, GetVersion, GetTheme  # local module but up one directory hence the sys path append ..

### constants ###

VersionFile = "../VERSION"  # Last Update YY.MM.DD
output_html="county-output.html" # relative per population per 100K - THIS IS ORIGINAL PLOT
output_html_1="county-output-raw.html" # just raw results (Added later so its output_html_1) - THIS IS NEW PLOT
SHOW_TOP_NUMBER=12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
ThemeFile = "../PLOTLY_THEME" # contents are comma sep: theme,font family,font size
updatedate_dt = datetime.datetime.now()
updatedate_str = updatedate_dt.strftime("%Y-%m-%d %H:%M:%S")
csv_file = "CA-covid19cases_test.csv"
csv_file_parsable = "CA-covid19cases_test-parsable.csv"

# Get Version
Version = GetVersion(VersionFile)

# Get Theme
Theme_Template, Theme_Font, Theme_FontSize = GetTheme(ThemeFile)

# population file - NOTE: Now technically we don't need this as the information is in the CSV file
file_pop="county-pop.csv" # values from around 2020 good enough

# data input
# url_data="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv" # after March 12 2021 this data is deprecated with new data at new site
# old data site https://data.ca.gov/dataset/covid-19-cases points to new site https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state
url_data="https://data.chhs.ca.gov/dataset/f333528b-4d38-4814-bebb-12db1f10f535/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a/download/covid19cases_test.csv" # NEW

# read in covid data for california counties
c=pd.read_csv(url_data)
print(f"RECEIVED DATA (saved to {csv_file}):")
print()
print(f"{c.describe()=}")
print()
print(f"{c.head()=}")
print()
print(f"{c.columns=}")
c.to_csv(csv_file)
c = c.sort_values("DATE",ascending=True)

# population file
cpops = pd.read_csv(file_pop,index_col="Rank")

# get top 10 (or SHOW_TOP_NUMBER) of counties based on population + select which ones to show enabled on legend
top10 = cpops.head(SHOW_TOP_NUMBER)["County"]
visible_counties = top10.values.tolist() # essentially its ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda', 'Sacramento', 'Contra Costa', 'Fresno', 'Kern', 'San Francisco']
visible_counties = ['Los Angeles', 'Santa Clara', 'San Mateo', 'San Francisco', '0-California-State']
print()
print(f"top counties={top10.values.tolist()}")
print(f"visible_counties={visible_counties}")
print()

# list of tuples [(county,pop) (county,pop)]
cpops_county_list=cpops["County"].values.tolist()
cpops_pop_list=cpops["Population"].values.tolist()
cpop_zip=zip(cpops_county_list,cpops_pop_list)
cpop_list=list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet

# Covid Data Manipulation to how we need the data

cols_to_select=["DATE","AREA","AREA_TYPE","CASES","DEATHS"]

cleandates_c = c[c["DATE"]!="NaN"]

adjusted_cleaned_c = cleandates_c[cols_to_select]
print()
print(f"{adjusted_cleaned_c=}")
print()

unique_areas = list(set(cleandates_c["AREA"].values.tolist()))
print()
print(f"{unique_areas=}")
print()

cnew = pd.DataFrame(columns = ["DATE","AREA","AREA_TYPE","CASES","DEATHS","TOTALCASES","TOTALDEATHS"])

for i,v in enumerate(unique_areas):
    print("** DEBUG: mini dataframe to create cumulative - ", i, v)
    cpart = adjusted_cleaned_c[adjusted_cleaned_c["AREA"]==v]
    cpart = cpart.set_index("DATE")
    cpart["TOTALCASES"] = cpart["CASES"].cumsum()
    cpart["TOTALDEATHS"] = cpart["DEATHS"].cumsum()
    cpart = cpart.reset_index()
    print(cpart.tail())
    print()
    cnew = cnew.append(cpart, ignore_index = True)

print("* DEBUG: put together a dataframe with cumulative columns")
print(f"{cnew=}")

# cols to select has been adjusted now
cols_to_select=["DATE","AREA","AREA_TYPE","CASES","DEATHS","TOTALCASES","TOTALDEATHS"]

# Clean up - get counties only
clean_county_c = cnew[cnew["AREA_TYPE"]=="County"].dropna(subset=cols_to_select)
print("* DEBUG: final clean counties")
print(f"{clean_county_c=}")


# GET CALIFORNIA STATE

cali0 = cnew[cnew["AREA_TYPE"]=="State"].dropna(subset=cols_to_select)

clean_cali_c = cali0.replace("California","0-California-State")
print("* DEBUG: final clean california")
print(f"{clean_cali_c=}")

# THE FINAL COMBINED DATA:
final_c_and_cali = clean_county_c.append(clean_cali_c,ignore_index=True) # since indexes never got messed with this in these processes we can just remove ignore_index and keep its default as False but it doesn't hurt to keep
# sidenote manually added in this line to county-pop.csv - whatever its not the prettiest i don't care: # 59,0-California-State,40129160
# adding california in - finish

# OKAY LETS SORT IT AND NOW ITS FINAL
c = final_c_and_cali.sort_values(by=['DATE']) # sort by date

print()
print(f"CONVERTED TO PARSABLE DATA (saved to {csv_file_parsable}):")
print()
print(f"{c.describe()=}")
print()
print(f"{c.tail()=}")
print()
print(f"{c.columns}")
c.to_csv(csv_file_parsable)


###################################################
#              PLOTTING                           #
###################################################

# * plotly init
print()
print(f"- plotting start (theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize})")
print()
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
# subplots
fig = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all
fig_1 = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles_1, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all
random_county = cpops_county_list[0] # we picked top one which is LA (most populous at the top)
last_x = c[c.AREA == random_county]["DATE"].values.tolist()[-1]
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

predictnote =  f", <b>Note:</b> Prediction uses {predictdays} day linear fit, appears as black-dashed line."
fig.update_layout(title=f"<b>California Counties Covid19 Stats (Relative to Population Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str} {predictnote}",**plot_options) # main title & theme & hover options & font options unpacked
fig_1.update_layout(title=f"<b>California Counties Covid19 Stats (Normal / Raw Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str}  {predictnote}",**plot_options) # main title & theme & hover options & font options unpacked

# * consider each county and trace it on plotly
color_index = -1 # color index, if we set to None then we alternate colors for every trace. if we set to -1 here then we match color of prediction

for county,pop in cpop_list:
    graph_options = { "fig": fig,
        "fig_1": fig_1,
        "area": county,
        "pop": pop,
        "c": c,
        "nX": "DATE",
        "nA": "AREA",
        "nC": "TOTALCASES",
        "nD": "TOTALDEATHS",
        "nNC": "CASES",
        "nND": "DEATHS",
        "visible_areas": visible_counties,
        "color_index": color_index }
    fig, fig_1, color_index = graph4area(**graph_options)
    print()

# * plotly generate html output generation
fig.write_html(output_html,auto_open=False)
fig_1.write_html(output_html_1,auto_open=False)

# * html div generation (not used)
div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
div_1 = plotly.offline.offline.plot(fig_1, show_link=False, include_plotlyjs=False, output_type='div')
print(f"size of type & div of relative plot - type(div)={type(div)} len(div)={len(div)}") # div not used
print(f"size of type & div of normal plot - type(div_1)={type(div_1)} len(div)={len(div_1)}") # div not used
print()

# the end
print("- plotting end")

### END
