import json
import urllib.request
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline.offline
import os
import datetime
import bs4
import htmlmin
import pickle
from common import avgN, Entry, Country, GetVersion, GetTheme, THOUSAND, PER, PER_TEXT
import pandas as pd
import math

# By: Kostia Khlebopros
# Site: http://www.infotinks.com/coronavirus-dashboard-covid19-py/
# Github: https://github.com/bhbmaster/covid19

### constants ###

VersionFile = "VERSION"  # Last Update YY.MM.DD
SITE="https://pomber.github.io/covid19/timeseries.json"
start_time = datetime.datetime.now()
start_time_string = start_time.strftime("%Y-%m-%d %H:%M:%S")
start_time_posix = start_time.strftime("%Y-%m-%d-%H-%M-%S")
bootstrapped = False
sigdigit=5
sigdigit_small=2
predict_days_min=5
predict_days_max=15
TESTDATA = "code/CountryTestData.json"
moving_average_samples = 7 # 7 day moving average for daily new cases and daily deaths
days_predict_new_cases = 30
ThemeFile = "PLOTLY_THEME" # contents are comma sep: theme,font family,font size
POPFILE = "world-pop.csv"

# Get Version:
Version = GetVersion(VersionFile)

# Get Theme
Theme_Template, Theme_Font, Theme_FontSize = GetTheme(ThemeFile)

### functions ###

# if need to round a number that might also be None. n is the number, places is number of decimal places. if 0 places we use thousand seperators
def round_or_none(n,places,sep=True):
    try:
        if places == 0:
            return f"{int(n):,}"
        else:
            return f"{n:0.{places}f}"
    except:
        return None

# create divs of graph of a certain type from country class item

def graph2div(country_class,graph_type,relative=False):

    # note relative is the want to do relative plots, i.relative_possible is if its possible (assuming population is not None and a number above 0)

    i=country_class

    if relative:
        the_rel_string="-perpop"
        the_rel_string_camel=" Population Relative" if i.relative_possible else "" # only show it in title if we have population data otherwise its regular plot (but we still print to -perpop file; no biggy; thats good)
    else:
        the_rel_string=""
        the_rel_string_camel=""

    if graph_type=="log":           # log
        the_type_string="LOG"+the_rel_string                   # FILENAME
        the_type_string_camel="Log"+the_rel_string_camel       # PLOT TITLE
        the_type_fig="log"
    else:                           # normal
        the_type_string="NORMAL"+the_rel_string                # FILENAME
        the_type_string_camel="Normal"+the_rel_string_camel    # PLOT TITLE
        the_type_fig=None

    # construct filename
    country_name=i.country
    shortfile_name=f"{i.countryposix}-plot-{the_type_string}.html"
    full_path_html=f"html-plots/{shortfile_name}"

    # population string for title shown if there is population value (relative_possible is true)
    population_number_string = f"{int(i.population):,}" if i.relative_possible else "N/A"
    population_string = f"(pop. {population_number_string})"

    # subplot string shown if relative and relative possible
    pop_per_string = f" per {PER_TEXT} people" if relative and i.relative_possible else ""

    # give subplot titles
    subplot_titles = (f"<b>Cases, Deaths, Recovered, Active{pop_per_string}</b>",f"<b>Death & Recovery %</b>",
    f"<b>Daily Cases & {days_predict_new_cases}-day Linear Prediction{pop_per_string}</b>",f"<b>Daily Deaths{pop_per_string}</b>")
    spacing = 0.035

    # make the 4 subplots 2x2
    fig = make_subplots(rows=2, cols=2, horizontal_spacing=spacing, vertical_spacing=spacing, subplot_titles=subplot_titles,shared_xaxes=True)

    # supported fonts: https://plotly.com/python/reference/layout/
    plot_options={
        "hoverlabel_font_size": Theme_FontSize,
        "title_font_size": Theme_FontSize+2,
        "legend_font_size": Theme_FontSize,
        "font_size": Theme_FontSize,
        "hoverlabel_font_family": Theme_Font,
        "title_font_family": Theme_Font,
        "legend_font_family": Theme_Font,
        "font_family": Theme_Font,
        "hoverlabel_namelength": -1,  # the full line instead of the default 15
        "hovermode": "x", # old method was but hard to keep track of them 'x unified',
        "template": Theme_Template
    }

    # y values:
    CASES_LIST = i.rel_cases_list if relative and i.relative_possible else i.cases_list
    DEATHS_LIST = i.rel_deaths_list if relative and i.relative_possible else i.deaths_list
    ACTIVE_LIST = i.rel_active_list if relative and i.relative_possible else i.active_list
    RECOVERED_LIST = i.rel_recovered_list if relative and i.relative_possible else i.recovered_list
    DEATH_PERCENT_LIST = i.rel_death_percent_list if relative and i.relative_possible else i.death_percent_list
    RECOVERY_PERCENT_LIST = i.rel_recovery_percent_list if relative and i.relative_possible else i.recovery_percent_list
    DELTA_CASES_LIST = i.rel_delta_cases_list if relative and i.relative_possible else i.delta_cases_list
    DELTA_DEATHS_LIST = i.rel_delta_deaths_list if relative and i.relative_possible else i.delta_deaths_list

    # TEST DEBUG
    # if i.country == "US":
    #     print(f"DEBUG: {i.country=} {relative=} {i.relative_possible=} {i.population=} {CASES_LIST=}")

    # Note: instead of Diff it used to say Δ, but that renders weird on html (I tried to fix it but too much work for something small)

    # plot title
    fig.update_layout(title=f"<b>{country_name}</b> {population_string} - <b>Covid19 {the_type_string_camel} Plots</b> - covid19plot.py v{Version}<br><b>Last Data Point:</b> {i.last_date} , <b>Updated On:</b> {start_time_string}",**plot_options)

    # add all of the traces to the plots
    fig.add_trace(go.Scatter(x=i.date_list, y=CASES_LIST, name=f"<b>Cases</b> : y<sub>fin</sub>={round_or_none(CASES_LIST[-1],0)}", line=dict(color='firebrick', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=DEATHS_LIST, name=f"<b>Deaths</b> : y<sub>fin</sub>={round_or_none(DEATHS_LIST[-1],0)}", line=dict(color='red', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=RECOVERED_LIST, name=f"<b>Recovered</b> : y<sub>fin</sub>={round_or_none(RECOVERED_LIST[-1],0)}", line=dict(color='green', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=ACTIVE_LIST, name=f"<b>Active Cases</b> : y<sub>fin</sub>={round_or_none(ACTIVE_LIST[-1],0)}", line=dict(color='purple', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=DEATH_PERCENT_LIST, name=f"<b>Death %</b> : y<sub>fin</sub>={round_or_none(DEATH_PERCENT_LIST[-1],2)}%", showlegend=True),row=1,col=2)

    fig.add_trace(go.Scatter(x=i.date_list, y=RECOVERY_PERCENT_LIST, name=f"<b>Recovery %</b> : y<sub>fin</sub>={round_or_none(RECOVERY_PERCENT_LIST[-1],2)}%", showlegend=True),row=1,col=2)

    # new daily cases
    fig.add_trace(go.Scatter(x=i.date_list, y=DELTA_CASES_LIST, name=f"<b>New Cases</b> : y<sub>fin</sub>={round_or_none(DELTA_CASES_LIST[-1],0)}", showlegend=True),row=2,col=1)

    # getting moving average of new daily cases
    xavg,yavg = avgN(moving_average_samples,i.date_list,DELTA_CASES_LIST)

    fig.add_trace(go.Scatter(x=xavg, y=yavg, name=f"<b>New Cases {moving_average_samples}day Moving Avg</b> : y<sub>fin</sub>={round_or_none(yavg[-1],0)}", showlegend=True),row=2,col=1) # when had OLD-MIDDLE-ROW this was row=3,col=1

    success, xfinal, yfinal, r_sq, m, b0 = i.lastXdayslinearpredict(yavg, days_predict_new_cases)

    # print(f"DEBUG: fit -> success={success} fita={fita} fitb={fitb} fitc={fitc}")
    # print(f"DEBUG: fit -> xfinal={xfinal} yfinal={yfinal}")

    if success:

        # predict when cross y=0

        if m != 0: # don't calc crossing if slope is 0 or flat, as its not existant
            try:
                y_to_cross = 0.0 # target y to cross (find which X equals at the Y value)
                x_cross1 = (y_to_cross - float(b0)) / float(m)   # y=mx+b   ->   x=(y-b)/m
                x_cross1_int=int(x_cross1)  # convert to int value (as we need 1 day or 3 day from day0 type of thing)
                day0=xfinal[0]  # this is x0 essentially and its a date
                day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")  # convert to date time date so we can add x_cross to it
                daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))  # get the date when we cross by adding x_cross to day0
                daycross = daycrossdt.strftime("%Y-%m-%d")  # convert to easy to understand text
            except Exception as e:
                daycross = None
                print(f"* WARNING IN FIT PLOT: Couldn't calculate fit for {shortfile_name} because: {e}")
        else:
            daycross = None

        if relative and i.relative_possible:
            i.rel_predict_date_zero = daycross  # this variable doesn't exist in Country class, but in python you can create it regardless (we call it later when creating the HTML)
        else:
            i.predict_date_zero = daycross  # this variable doesn't exist in Country class, but in python you can create it regardless (we call it later when creating the HTML)

        if daycross != None: # we could have successfully fitted but cross date could be weird so we need to check if daycross is none
            fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"<b>Daily New Cases {days_predict_new_cases} Days Prediction</b><br>r<sup>2</sup>={r_sq:0.5f}<br>y={m:0.3f}x+{b0:0.1f} where x<sub>0</sub>={xfinal[0]}<br>y=0 / no new cases predicted @ {daycross}", line=dict(color='black', width=1, dash='dash'), showlegend=True), row=2,col=1) # when had OLD-MIDDLE-ROW this was row=3,col=1

    # daily deaths
    fig.add_trace(go.Scatter(x=i.date_list, y=DELTA_DEATHS_LIST, name=f"<b>New Deaths</b> : y<sub>fin</sub>={round_or_none(DELTA_DEATHS_LIST[-1],0)}", showlegend=True),row=2,col=2) # when had OLD-MIDDLE-ROW this was row=3,col=1

    # daily deaths moving average
    xavg,yavg = avgN(moving_average_samples,i.date_list,DELTA_DEATHS_LIST)

    fig.add_trace(go.Scatter(x=xavg, y=yavg, name=f"<b>New Deaths {moving_average_samples}day Moving Avg</b> : y<sub>fin</sub>={round_or_none(yavg[-1],0)}", showlegend=True),row=2,col=2) # when had OLD-MIDDLE-ROW this was row=3,col=1

    # adjust the plot axes properly

    fig.update_yaxes(type=the_type_fig,row=1,col=1)

    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=1)

    fig.update_yaxes(type=None,row=1,col=2) # new plot

    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=2) # new plot

    # write to HTML & DIV string which we return

    fig.write_html(full_path_html,auto_open=False) # write 2.5 MiB html file

    div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')

    # return the div string

    return div

# create html file out of div list

def divs2html(div_list,type_title,time_string,output_file,bootstrap_on=False):

    # type_title has to be Normal or Log

    # if relative is stored in div_list in first items 3rd index
    relative = div_list[0][2]
    relative_title_string = f" - Relative to Population per {PER_TEXT} People" if relative else ""

    if type_title == "Normal":
        other_type_title="Log"
        countersite="https://hitwebcounter.com/counter/counter.php?page=7650825&style=0024&nbdigits=9&type=page&initCount=1020"
    else:
        other_type_title="Normal"
        countersite="https://hitwebcounter.com/counter/counter.php?page=7650826&style=0024&nbdigits=9&type=page&initCount=1020"

    bootstrap_string="""<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">\n""" if bootstrap_on else ""

    country_count=len(div_list)-1
    last_date=div_list[0][0].last_date   # first countries/items last date should be the same as the rest

    # ~~~ start of html ~~~ #

    # html = """<!DOCTYPE html>                # with html5 the divs are 50% height, without this they are 100%

    html = f"""<html>
                <head>
                    <title>Covid19Plot.py Plots {type_title} Scale{relative_title_string}</title>
                    {bootstrap_string}
                    <meta name="author" content="Kostia Khlebopros">
                    <!-- pace.js progress bar js & css style : local version present, but we load from cloud for speed -->
                    <script src="https://cdn.jsdelivr.net/npm/pace-js@latest/pace.min.js"></script>
                    <link href="./code/pace-big-counter.css" rel="stylesheet">
                    <!-- plotly and jquery : local version present, but we load from cloud for speed -->
                    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                    <style>
                        h2, h3, p, table, input {{
                            margin-left: 40px;
                        }}
                        td {{
                            text-align: center;
                        }}
                        .roundback {{
                            border-radius: 25px;
                            background: #ccc;
                            padding: 10px;
                        }}
                        .bigger {{
                            padding: 20px;
                        }}
                        .dropdown-content {{
                            margin-left: 40px;
                        }}
                        .roundback-green {{
                            border-radius: 25px;
                            background: #90EE90;
                            padding: 10px;
                        }}
                        .roundback-blue {{
                            border-radius: 25px;
                            background: #AFEEEE;
                            padding: 10px;
                        }}
                    </style>
                <head/>
                <body>
                    <h2 class="roundback bigger"><u>Covid19Plot.py Country {type_title} Plots{relative_title_string}</u> - v{Version}</h2>
                    <p><b>Last Data Point:</b> {last_date} , <b>Updated On:</b> {time_string}</p>
                    <p>* <b>Caution - Page might take a long moment to load: </b> this is a large HTML file (over 20 MiB). The loading progress percentage is at top right corner; it might hover around 99%, please be patient as it will finish. If the progress percentage not shown, just wait for browser to awknowledge the page is done loading.</p>
                    <p>* <b>Other Plots:</b></p>
                    <!-- <p>- <a href='covid19-{other_type_title.lower()}.html'>Click here to see <b>Covid19Plot.py Country {other_type_title} Plots</b>.</a></p> -->
                    <p>- <a href='covid19-normal.html'>Click here to see <b>Covid19Plot.py Country Normal Plots</b>.</a></p>
                    <p>- <a href='covid19-normal-perpop.html'>Click here to see <b>Covid19Plot.py Country Normal Relative to Population Plots</b>.</a></p>
                    <p>- <a href='covid19-log.html'>Click here to see <b>Covid19Plot.py Country Log Plots</b>.</a></p>
                    <p>- <a href='covid19-log-perpop.html'>Click here to see <b>Covid19Plot.py Country Log Relative to Population Plots</b>.</a></p>
                    <p>- <a href='usa-states/states-output.html'>Click here to see <b>USA States Daily & Total Plots (relative to population with 7 day moving average)</b>.</a></p>
                    <p>- <a href='usa-states/states-output-raw.html'>Click here to see <b>USA States Daily & Total Plots (raw normal data with 7 day moving average)</b>.</a></p>
                    <p>- <a href='usa-ca/county-output.html'>Click here to see <b>California's Counties Daily & Total Plots (relative to population with 7 day moving average)</b>.</a></p>
                    <p>- <a href='usa-ca/county-output-raw.html'>Click here to see <b>California's Counties Daily & Total Plots (raw normal data with 7 day moving average)</b>.</a></p>
                    <p>- <a href='canada/canada-output.html'>Click here to see <b>Canada's Provinces & Territories Daily & Total Plots (relative to population with 7 day moving average)</b>.</a></p>
                    <p>- <a href='canada/canada-output-raw.html'>Click here to see <b>Canada's Provinces & Territories Daily & Total Plots (raw normal data with 7 day moving average)</b>.</a></p>
                    <p>* <b>How To Use:</b> Scroll down to the country of inquiry via "Quick Navigation" or scroll manually. To get an interactive plot open the "Normal" or "Log" link - which opens the countries plot seperately, the plots are fully interactive when displayed seperately. The different lines / traces can enabled, disabled, all-enabled ,or one-enabled by clicking and double clicking on the legend items. The California county plots are also similarly interactive.</p>
                    <p>* <b>Source Code & Other Links:</b> available on <a href="https://github.com/bhbmaster/covid19">GitHub</a> and <a href="http://www.infotinks.com/coronavirus-dashboard-covid19-py/">infotinks.com</a></p>
                    <p>* <b>Diff Change</b> or <b>Delta</b> is change from previous day ( + is growth; - is reduction )</p>
                    <p>* <b>Ratio Diff Change</b> or <b>Ratio</b> is % change from previous day ( 1 or higher is growth; 0 to 1 is reduction )</p>
                    <p>* <b>Note:</b> Each countries covid stats and plots are shown one by one. Countries are sorted by total cases in increasing order, so the country in #1 is the leader in most covid cases to date.</p>
                    <p>* <b>Note:</b> The very first 'country' to be shown is actually not a country but the world total represented as "TOTAL". It will always have the highest number of cases, as its the sum of all countries, so its takes spot #0 at the very top.</p>
                    <p>* <b>Note:</b> Peak active case prediction date is calculated using a linear regression fit on "active cases ratio" and examing its past X days values to see when it crosses 1.0.</p>
                    <p>* An r<sup>2</sup> closer to 1.0 means a better prediction.</p>
                    <p>* Ignore predictions with past dates.</p>
                    <p>* <b>Note:</b> Daily new cases moving average has a linear regression fit calculated from previous {days_predict_new_cases} days and extending same days into the future. This is to help estimate daily new cases trend. Of course, the real trend is not linear, so this is strictly a prediction. The predicted line has its r<sup>2</sup> fit value and y=mx+b equation shown in the legend. x is number of days since x<sub>0</sub>, which is provided in the label. y is predicted daily new cases (technically its the predicted moving average of the daily new cases). Finally, we predict the day we reach 0 daily new cases; also shown on the legend.</p>
                    <p>* <b>Note:</b> The plotly graphs are interactive. To have better you can click on the "Normal" or "Log" link for each country to see it's own interactive plot.</p>
                    <p>There you can control control which information is plotted by clicking & double clicking on the items in the legend to isolate or disable that data.</p>
                    <p>* <b>Note:</b> Active Cases is calculated by subtracting Recovered and Deaths from total Cases.</p>
                    <p>* <b>Note:</b> The United States, US, recovery numbers are all nullfied to 0 on 2020-12-15 and onward. This was a decision made by the data source. More can be read here: <a href="https://github.com/CSSEGISandData/COVID-19/issues/3464">Github Issue</a> and <a href="https://covidtracking.com/about-data/faq#why-have-you-stopped-reporting-national-recoveries">Reasoning</a>.</p>
                    <p>* <b>World Data Source:</b> The world data is gathered directly from <a href="https://pomber.github.io/covid19/">Pomber</a> which generates a parsable <b><a href="{SITE}">json</a></b> daily. They use the data from <a href="https://github.com/CSSEGISandData/COVID-19">CSSEGISandData</a> data to generate that json.</p>
                    <p>* <b>USA States Source:</b> The US data is gathered directly from <a href="https://github.com/nytimes/covid-19-data">NY Times</a> which generates a parsable <b><a href="https://github.com/nytimes/covid-19-data/blob/master/us-states.csv">csv</a></b> daily.</p>
                    <p>* <b>California Data Source (CURRENT DATA):</b> The California county data is gathered from <a href="https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state">data.chhs.ca.gov</a>, they also provide a parseable <b><a href="https://data.chhs.ca.gov/dataset/f333528b-4d38-4814-bebb-12db1f10f535/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a/download/covid19cases_test.csv">csv file</a></b> format.</p>
                    <p>* <b>California Data Source (DEPRECATED as of March 12, 2021):</b> The California county data is gathered from <a href="https://data.ca.gov/dataset/covid-19-cases/resource/926fd08f-cc91-4828-af38-bd45de97f8c3">data.ca.gov</a>, they also provide a parseable <b><a href="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv">csv file</a></b> format.</p>
                    <p>* <b>Canada Data Source (CURRENT DATA):</b> The Canada data is gathered directly from <a href="https://opencovid.ca/">COVID-19 Canada Open Data Working Group </a> which generates a parsable <b><a href="https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/cases_pt.csv">cases csv</a></b> and <b><a href="https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/deaths_pt.csv">deaths csv</a></b> daily.</p>
                    <p>* <b>Canada Data Source (DEPRECATED as of August 12, 2022):</b> The Canada data is gathered directly from <a href="https://github.com/ccodwg/Covid19Canada">COVID-19 Canada Open Data Working Group </a> which generates a parsable <b><a href="https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_prov/active_timeseries_prov.csv">csv</a></b> daily. Data source was deprecated as it stopped getting updated in May of 2022.</p>
                    <p>* <b>Note:</b> Antarctica population ranges from 1000 to 5000 based. I used the higher value.</p>
                    <a id="search_anchor"></a>
                    <h3 class="roundback">Country Quick Navigation / Search</h3>
                      <div id="search_links_div" class="dropdown-content">
                        <input type="text" placeholder="Search {country_count} Countries..." id="search_textbox" onkeyup="filterFunction()">
                         * <a href='#TOTAL' class='countrylinks'>(0) TOTAL</a>
            """
    # create all of the a links for the diff countries (alphabetical)

    search_list = [] # [(place,name,posixname),...]
    for index,value in enumerate(div_list):
        search_list.append( (index,value[0].country,value[0].countryposix) )

    searchbox_divlist = search_list[1:] # excluding TOTAL as we want that at front (already did; see above)
    searchbox_divlist.sort(key=lambda x: x[2])

    for place_number,country_name,country_posix_name in searchbox_divlist:
        html += f" * <a href='#{country_posix_name}' class='countrylinks'>({place_number}) {country_name}</a>"

    html += """</div>\n"""

    # print("HTML START:")
    # print(html)
    # print("HTML END:")

    place_num = -1 # so it starts at 0

    for country,div,relative in div_list:

        place_num += 1

        # to show per population bool
        show_pop_bool = country.relative_possible and relative

        # cases
        try:
            # ldr_cases = round(country.rel_last_delta_ratio_cases if show_pop_bool else country.last_delta_ratio_cases, sigdigit) # commented out because delta ratio should be same w and wout relative
            ldr_cases = round(country.last_delta_ratio_cases, sigdigit)
        except:
            # ldr_cases = country.rel_last_delta_ratio_cases if show_pop_bool else country.last_delta_ratio_cases # commented out because delta ratio should be same w and wout relative
            ldr_cases = country.last_delta_ratio_cases

        # deaths
        try:
            # ldr_deaths = round(country.rel_last_delta_ratio_deaths if show_pop_bool else country.last_delta_ratio_deaths, sigdigit) # commented out because delta ratio should be same w and wout relative
            ldr_deaths = round(country.last_delta_ratio_deaths, sigdigit)
        except:
            # ldr_deaths = country.rel_last_delta_ratio_deaths if show_pop_bool else country.last_delta_ratio_deaths # commented out because delta ratio should be same w and wout relative
            ldr_deaths = country.last_delta_ratio_deaths

        # recovered
        try:
            # ldr_recovered = round(country.rel_last_delta_ratio_recovered if show_pop_bool else country.last_delta_ratio_recovered, sigdigit) # commented out because delta ratio should be same w and wout relative
            ldr_recovered = round(country.last_delta_ratio_recovered, sigdigit)
        except:
            # ldr_recovered = country.rel_last_delta_ratio_recovered if show_pop_bool else country.last_delta_ratio_recovered # commented out because delta ratio should be same w and wout relative
            ldr_recovered = country.last_delta_ratio_recovered

        # active
        try:
            # ldr_active = round(country.rel_last_delta_ratio_active if show_pop_bool else country.last_delta_ratio_active, sigdigit) # commented out because delta ratio should be same w and wout relative
            ldr_active = round(country.last_delta_ratio_active, sigdigit)
        except:
            # ldr_active = country.rel_last_delta_ratio_active if show_pop_bool else country.last_delta_ratio_active # commented out because delta ratio should be same w and wout relative
            ldr_active = country.last_delta_ratio_active

        # type_title comes in as Log (doesn't work) turns to LOG (works), comes in as Normal (doesn't work )turns to NORMAL (works)
        # html += f"        <h3><a href='html-plots/{country.countryposix}-plot-{type_title.upper()}.html'>{country.country}</a></h3>\n"

        # population string
        pop_number_string = f"{int(country.population):,}" if country.relative_possible else "N/A"
        pop_string = f"(pop. {pop_number_string})"

        # country title
        html += f"<a id='{country.countryposix}'></a><h3 class='roundback'><u>#{place_num}. {country.country} {pop_string}</u> - <a href='#search_anchor'>Back To Search / Top</a></h3>\n"

        # links to other plots
        html += f"<p>More Plots: <a href='html-plots/{country.countryposix}-plot-NORMAL.html'>Normal</a> | <a href='html-plots/{country.countryposix}-plot-NORMAL-perpop.html'>Normal-PerPop</a> | <a href='html-plots/{country.countryposix}-plot-LOG.html'>Log</a> | <a href='html-plots/{country.countryposix}-plot-LOG-perpop.html'>Log-PerPop</a></p>"

        # message on if data is relative
        html += f"<p class='roundback-green'><b>Data & plots for country below is adjusted relative to the population per {PER_TEXT} people.</b></p>" if show_pop_bool else f"<p class='roundback-blue'><b>Data & plots for country below is raw data.</b></p>" 

        # TABLEROUND function used for table to roun relative to population values
        def TABLEROUND(x):
            try:
                return round(x,sigdigit)
            except:
                return x

        # Tables and strings

        html += f"""
                                <table border="1" cellpadding="5">
                                <tbody>
                                <tr>
                                <td><b>Data Date: {country.last_date}</b></td>
                                <td><b>Current</b></td>
                                <td><b>Diff Change</b> w/ last day</td>
                                <td><b>Ratio Diff Change</b> w/ last day</td>
                                </tr>
                                <tr>
                                <td>Cases</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_cases) if show_pop_bool else country.last_cases)}</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_delta_cases) if show_pop_bool else country.last_delta_cases)}</td>
                                <td>{THOUSAND(ldr_cases)}</td>
                                </tr>
                                <tr>
                                <td>Deaths</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_deaths) if show_pop_bool else country.last_deaths)}</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_delta_deaths) if show_pop_bool else country.last_delta_deaths)}</td>
                                <td>{THOUSAND(ldr_deaths)}</td>
                                </tr>
                                <tr>
                                <td>Recovered</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_recovered) if show_pop_bool else country.last_recovered)}</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_delta_recovered) if show_pop_bool else country.last_delta_recovered)}</td>
                                <td>{THOUSAND(ldr_recovered)}</td>
                                </tr>
                                <tr>
                                <td>Active Cases</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_active) if show_pop_bool else country.last_active)}</td>
                                <td>{THOUSAND(TABLEROUND(country.rel_last_delta_active) if show_pop_bool else country.last_delta_active)}</td>
                                <td>{THOUSAND(ldr_active)}</td>
                                </tr>
                                </tbody>
                                </table>\n
        """

        # death & recovery percent

        # deaths %
        try:
            # lp_deaths = round(country.rel_last_death_percent if show_pop_bool else country.last_death_percent, sigdigit_small) # commented out because delta ratio should be same w and wout relative
            lp_deaths = round(country.last_death_percent, sigdigit_small)
        except:
            # lp_deaths = country.rel_last_death_percent if show_pop_bool else country.last_death_percent # commented out because delta ratio should be same w and wout relative
            lp_deaths = country.last_death_percent

        # recovery %
        try:
            # lp_recovered = round(country.rel_last_recovery_percent if show_pop_bool else country.last_recovery_percent, sigdigit_small) # commented out because delta ratio should be same w and wout relative
            lp_recovered = round(country.last_recovery_percent, sigdigit_small) 
        except:
            # lp_recovered = country.rel_last_recovery_percent if show_pop_bool else country.last_recovery_percent # commented out because delta ratio should be same w and wout relative
            lp_recovered = country.last_recovery_percent

        html += f"""<p>* Last percent <b>recovered</b> from all cases: <b>{lp_recovered}%</b></p>
        <p>* Last percent <b>dead</b> from all cases: <b>{lp_deaths}%</b></p>\n"""

        #  ~~~ below - active new cases prediction ~~~ #

        # For predictions we don't need to do anything w/ respect to relative as the date cross values should be the same

        html += f"<p>* Predict <b>0 New Daily Cases</b> date</b> using {days_predict_new_cases} day linear regression: <b>{country.predict_date_zero}</b></p>"

        # # ~~~ above - active new cases prediction ~~~ # TO UNCOMMENT START SELECTION HERE

        # # ~~~ below - ratio prediction ~~~ #

        # predict_list=[]

        # for pdays in range(predict_days_min,predict_days_max+1):

        #     success, xfinal, yfinal, r_sq, m, b0 = country.lastXdayslinearpredict(country.delta_ratio_active_list, pdays)

        #     daycross=None
        #     r_sq=None

        #     if success:

        #         try:
        #             x_cross1 = (1.0 - float(b0)) / float(m)
        #             x_cross1_int=int(x_cross1)
        #             day0=xfinal[0]
        #             day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")
        #             daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))
        #             daycross = daycrossdt.strftime("%Y-%m-%d")
        #             # html += f"<p>* Using past {pdays} days for prediction, Active Cases might peak on {daycross}. The r^2 for this fit is {round(r_sq,sigdigit)}</p>\n"
        #         except:
        #             success=False

        #     predict_item=[pdays,success,daycross,None if r_sq == None else round(r_sq,sigdigit)]

        #     predict_list.append(predict_item)

        # html += """<p><b>Active Case Peak Prediction</b>: using past X days of "active case ratio" in a linear regression fit algorithm</p>
        # <table border="1" cellpadding="5">
        # <tbody>
        # <tr>
        # <td>past days</td>\n"""

        # for a in predict_list:
        #     html += f"<td>{a[0]}</td>\n"

        # html += """</tr>
        # <tr>
        # <td>predicted peak date</td>\n"""

        # for a in predict_list:
        #     html += f"<td>{a[2]}</td>\n"

        # html += """</tr>
        # <tr>
        # <td>r<sup>2</sup></td>\n"""

        # for a in predict_list:
        #     html += f"<td>{a[3]}</td>\n"

        # html += """</tr>
        # </tbody>
        # </table>\n"""

        # # ~~~ above prediction ~~~ # TO UNCOMMENT END SELECTION HERE

        # add the plot

        html += "        " + div+"\n"

        # redundant (already in notes # html += '<p>* <b>Note:</b> Data Source: <a href="https://pomber.github.io/covid19/">Pomber</a>, which generates daily json from <a href="https://github.com/CSSEGISandData/COVID-19">CSSEGISandData</a> data.</p>\n'

    html += f"""
                    <!-- hitwebcounter Code START -->
                    <a href="https://www.hitwebcounter.com" target="_blank">
                    <img src="{countersite}" title="Views:" Alt="hitwebcounter" border="0" >
                    </a>
                </body>
    """
    html += """
                <script>
                    function filterFunction() {
                      var input, filter, ul, li, a, i;
                      input = document.getElementById("search_textbox");
                      filter = input.value.toUpperCase();
                      div = document.getElementById("search_links_div");
                      a = div.getElementsByTagName("a");
                      for (i = 0; i < a.length; i++) {
                        txtValue = a[i].textContent || a[i].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                          a[i].style.display = "";
                        } else {
                          a[i].style.display = "none";
                        }
                      }
                    }
                </script>
            </html>
            """

    # ~~~ end of html ~~~ #

    # make it pretty (fix newlines, tabs, and spaces)
    prettyhtml = bs4.BeautifulSoup(html, "lxml").prettify()

    # make it htmlmin
    minihtml = htmlmin.minify(prettyhtml, remove_empty_space=True)

    # write file
    with open(output_file, 'wb') as file:
        file.write(minihtml.encode('utf-8'))

    # * Below method generated error on Windows because I use delta triangle but worked on MAC and LINUX
    # * ERROR: UnicodeEncodeError: 'charmap' codec can't encode character '\u0394' in position 4132: character maps to <undefined>
    # with open(output_file, 'w') as file:
    #     file.write(minihtml)

# save everything
def save_pickle(object_to_save,filename_prefix,time_string):
    if not os.path.exists("archived_data"):
        os.mkdir("archived_data")
    filename=f"archived_data/{filename_prefix}-{time_string}.pk"
    try:
        with open(filename,"wb") as file1:
            pickle.dump(object_to_save,file1)
    except:
        print(f"* failed to save object archived_data/{filename_prefix}-{time_string}.pk")

### main ###

def main():

    print("------------------------------")
    print(f"Covid19plot.py - v{Version}")
    print("------------------------------")
    print(f"- Plot theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize}")

    #### - GET DATA - METHOD 1 - START - ####
    # download json data (comment out this or load json; only have one)
    print(f"- Downloading json from {SITE} (please wait)")
    with urllib.request.urlopen(SITE) as url:
        data=json.loads(url.read().decode())
    if not data:
    	print(f"- Download Failed (no data)")
    print(f"- Download Complete")
    #### - GET DATA - METHOD 1 - END - ####

    #### - GET DATA - METHOD 2 - START ####
    # # load json data from file (comment out this or load json; only have one) - useful for testing and debugging
    # print(f"- Loading json from {TESTDATA}. (please wait)")
    # with open(TESTDATA) as f:
    #     data = json.load(f)
    # if not data:
    #     print(f"- Loading Failed (no data).")
    # print(f"- Loading Complete.")
    #### - GET DATA - METHOD 2 - END ####

    #### LOAD POPULATION DATA ####

    print(f"- Reading population csv from {POPFILE}")
    pop = pd.read_csv(POPFILE)

    #### PARSE BOTH DATA SETS POPULATION AND COVID ####

    list_of_countries=[]
    for x in data:
        str_country=x
        # get population value
        curpop_list = list(pop[pop["Country"] == x]["Population"].values) # if has value length 1 if no value length 0
        if len(curpop_list) > 0: # make sure there is an item in the list
            curpop_value = curpop_list[0]
            if not math.isnan(curpop_value): # also make sure the value is not NaN (also a missing value, probably a space or something)
                curpop = int(curpop_value)
            else:
                curpop = None
        else: # if no items then no population
            curpop = None
        if str_country == "Korea, South": # work around for south korea as its written "South Korea" in population file
            curpop = int(list(pop[pop["Country"] == "South Korea"]["Population"].values)[0])
        if curpop == None:
            print(f"* WARNING: Missing population data for {str_country=} {curpop=} in {POPFILE} file.")
        # print(f"{str_country=} {curpop=}")
        # work on covid data from json
        list_of_entries=[]
        oldEntry=None
        for i in data[x]:
            str_date=i["date"]
            int_confirmed=i["confirmed"]
            int_deaths=i["deaths"]
            int_recovered=i["recovered"]
            entry=Entry(str_date,int_confirmed,int_deaths,int_recovered,prevEntry=oldEntry)
            oldEntry=entry
            list_of_entries.append(entry)
        country=Country(str_country,list_of_entries,population=curpop)
        list_of_countries.append(country)
        # print(f"- {x} on {last_date} has {confirmed} confirmed {deaths} deaths {recovered} recovered {active} active")

    # print(f"* TOTALS on {last_date} are {last_confirmed} confirmed {last_deaths} deaths {last_recovered} recovered {last_active} active")
    print(f"* {len(list_of_countries)} countries + 1 world total = {len(list_of_countries)+1} total plots")

    # get world total country

    # world total not provided so we sum everything

    # get list of dates from China as it has the most - most likely (thats where it started so it will have most dates)
    all_dates=[]
    for i in list_of_countries:
        if i.country == "China":
            all_dates=i.date_list # at this point all_dates is all of our dates
            break

    # ### - DEBUG TEST DATA - START ####
    # # For quicker runs - for tests: only work with China, US and Canada by creating new list only w/ those countries
    # TestCountries = [ "China", "US", "Canada" ]
    # test_list_of_countries = []
    # print(f"* {len(TestCountries)} countries + 1 world total = {len(TestCountries)+1} total plots (modified for debug / testing)")
    # for i in list_of_countries:
    #     if i.country in TestCountries:
    #         test_list_of_countries.append(i)
    # list_of_countries = test_list_of_countries
    # ### - DEBUG TEST DATA - END ####

    # now iterate thru all of the dates summing each country at the date
    i=0
    oldEntry=None
    total_entry_list=[]
    for d in all_dates: # outer date loop (iterate thru all of the dates)
        total_confirmed=0
        total_deaths=0
        total_recovered=0
        for i in list_of_countries:  # country loop - itereate thru all countries
            for e in i.entrylist:    # inner date loop - itereate thru all the dates until we hit our date & break out of inner date loop
                if e.date == d:
                    total_confirmed+=e.cases
                    total_deaths+=e.deaths
                    total_recovered+=e.recovered
                    break
        total_entry=Entry(d,total_confirmed,total_deaths,total_recovered,prevEntry=oldEntry)
        total_entry_list.append(total_entry)
        oldEntry=total_entry
    WORLDPOPULATION = int(list(pop[pop["Country"] == "Earth"]["Population"].values)[0])
    total_country=Country("TOTAL",total_entry_list,population=WORLDPOPULATION)
    list_of_countries.append(total_country)

    # sort list of countries by total cases (TOTAL will be at top)
    list_of_countries.sort(key=lambda x: x.last_cases, reverse=True)

    #### CREATE DIRS AND PLOT DIV TEXTS ####

    rows=len(list_of_countries)

    # the div_lists below are of form # lists [(countryname,divs,relative_bool), (countryname,divs,relative_bool), ...]
    div_list_log = []
    div_list_normal = []
    div_list_log_perpop = []
    div_list_normal_perpop = []

    # make sure dirs exists incase we dump html plots (which we do) and image files (which we dont anymore actually - take too much space)
    if not os.path.exists("html-plots"):
        os.mkdir("html-plots")
    if not os.path.exists("img-plots"):
        os.mkdir("img-plots")

    # create divs for each country and store in lists

    for place, i in enumerate(list_of_countries):
        # normal
        div=graph2div(i,"normal") # by default relative=False (means not per pop)
        div_list_normal.append( (i, div, False) )
        # log
        div=graph2div(i,"log")  # by default relative=False (means not per pop)
        div_list_log.append( (i, div, False) )
        # normal per pop (means its relative)
        div=graph2div(i,"normal",relative=True)
        div_list_normal_perpop.append( (i, div, True) )
        # log per pop (means its relative)
        div=graph2div(i,"log",relative=True)
        div_list_log_perpop.append( (i, div, True) )
        # done creating div plots message
        print(f"{place}/{rows} - {i.country} (pop {i.population}) - last value from {i.last_date} with {i.last_cases} cases, {i.last_deaths} deaths, {i.last_recovered} recovered, {i.last_active} active cases.")

    ##### WRITE DIVS TO HTML FILES ####

    # create html from div list - normal
    filename = "covid19-normal.html"
    print(f"Creating '{filename}' - normal axis world covid plots, please wait.")
    divs2html(div_list_normal,"Normal",start_time_string,"covid19-normal.html",bootstrapped)

    # create html from div list - log
    filename = "covid19-log.html"
    print(f"Creating '{filename}' - log axis world covid plots, please wait.")
    divs2html(div_list_log,"Log",start_time_string,"covid19-log.html",bootstrapped)

    # create html from div list - normal
    filename = "covid19-normal-perpop.html"
    print(f"Creating '{filename}' - normal axis relative to population world covid plots, please wait.")
    divs2html(div_list_normal_perpop,"Normal",start_time_string,"covid19-normal-perpop.html",bootstrapped)

    # create html from div list - log
    filename = "covid19-log-perpop.html"
    print(f"Creating '{filename}' - log axis relative to population axis world covid plots, please wait.")
    divs2html(div_list_log_perpop,"Log",start_time_string,"covid19-log-perpop.html",bootstrapped)

    # save
    # save_pickle(list_of_countries,"country-class-list",start_time_posix)

    # complete message
    print("Generating plots & html done!")

if __name__ == "__main__":
    main()

### the end ###
