import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline.offline
import os
import datetime
import bs4
try:
    import htmlmin  # provided by htmlmin2 on Python 3.13+ (stdlib cgi was removed)
except ImportError:  # pragma: no cover - fallback if minify package is missing
    htmlmin = None
import pickle
from common import (
    avgN,
    Entry,
    Country,
    GetVersion,
    GetTheme,
    THOUSAND,
    PER,
    PER_TEXT,
    read_csv_from_url,  # kept so the commented live-download remnant below still works if uncommented
    read_csv_local,
    OWID_COMPACT_CSV,
    OWID_LOCAL_CSV,
    OWID_COVID_DOCS,
    OWID_COVID_PAGE,
    NYT_COVID_REPO,
    NYT_US_STATES_CSV,
    CHHS_CA_PAGE,
    CHHS_CA_CSV,
    NYT_US_COUNTIES_CSV,
    CANADA_OPENCOVID,
    CANADA_CASES_CSV,
    CANADA_DEATHS_CSV,
    POMBER_JSON,
    POMBER_PAGE,
    JHU_CSSE_REPO,
    CA_DATA_DEPRECATED_PAGE,
    CA_DATA_DEPRECATED_CSV,
    CANADA_DEPRECATED_REPO,
    CANADA_DEPRECATED_CSV,
)
import pandas as pd
import math

# By: Kostia Khlebopros
# Site: http://www.infotinks.com/coronavirus-dashboard-covid19-py/
# Github: https://github.com/bhbmaster/covid19

### constants ###

VersionFile = "VERSION"  # Last Update YY.MM.DD
SITE = OWID_COMPACT_CSV  # original online URL (shown in HTML footnotes)
# Used to download live: SITE was fetched with read_csv_from_url(SITE, ...)
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

# world-pop.csv still uses a few JHU/Pomber names. Map OWID names when we have to fall back to it.
OWID_TO_WORLD_POP = {
    "United States": "US",
    "Myanmar": "Burma",
    "Taiwan": "Taiwan*",
    "Vatican": "Holy See",
    "Palestine": "West Bank and Gaza",
    "Democratic Republic of Congo": "Congo (Kinshasa)",
    "Congo": "Congo (Brazzaville)",
    "Cote d'Ivoire": "Cote d'Ivoire",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Czech Republic": "Czechia",
    "Cape Verde": "Cabo Verde",
    "East Timor": "Timor-Leste",
    "Swaziland": "Eswatini",
    "Micronesia (country)": "Micronesia",
}

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
    fig.add_trace(go.Scatter(x=i.date_list, y=DELTA_CASES_LIST, name=f"<b>New Cases</b> : y<sub>fin</sub>={round_or_none(DELTA_CASES_LIST[-1] if DELTA_CASES_LIST else None,0)}", showlegend=True),row=2,col=1)

    # getting moving average of new daily cases
    xavg,yavg = avgN(moving_average_samples,i.date_list,DELTA_CASES_LIST)

    if yavg:
        fig.add_trace(go.Scatter(x=xavg, y=yavg, name=f"<b>New Cases {moving_average_samples}day Moving Avg</b> : y<sub>fin</sub>={round_or_none(yavg[-1],0)}", showlegend=True),row=2,col=1)

        success, xfinal, yfinal, r_sq, m, b0 = i.lastXdayslinearpredict(yavg, days_predict_new_cases)
    else:
        success, xfinal, yfinal, r_sq, m, b0 = False, None, None, None, None, None

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

    if yavg:
        fig.add_trace(go.Scatter(x=xavg, y=yavg, name=f"<b>New Deaths {moving_average_samples}day Moving Avg</b> : y<sub>fin</sub>={round_or_none(yavg[-1],0)}", showlegend=True),row=2,col=2)

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
                    <p>* <b>Note:</b> Active Cases is calculated by subtracting Recovered and Deaths from total Cases. The current world source does not publish recovered counts, so Recovered is 0 and Active is Cases minus Deaths.</p>
                    <p>* <b>Note:</b> Recovered counts used to be published by JHU CSSE via Pomber. The United States recovery numbers were nullified to 0 on 2020-12-15 and onward in that older source. More can be read here: <a href="https://github.com/CSSEGISandData/COVID-19/issues/3464">Github Issue</a> and <a href="https://covidtracking.com/about-data/faq#why-have-you-stopped-reporting-national-recoveries">Reasoning</a>.</p>
                    <p>* <b>World Data Source (CURRENT):</b> Bundled local snapshot of full historical country cases and deaths from <a href="{OWID_COVID_PAGE}">Our World in Data</a> (<code>data/owid-compact.csv</code>). Original compact COVID-19 <b><a href="{SITE}">CSV</a></b> (series starts 2020-01-01). Docs: <a href="{OWID_COVID_DOCS}">OWID COVID data</a>. World totals use OWID's World series rather than summing every location. Live download remnant is commented in <code>covid19plot.py</code>.</p>
                    <p>* <b>World Data Source (DEPRECATED as of 2023-03-09):</b> Previously gathered from <a href="{POMBER_PAGE}">Pomber</a> <b><a href="{POMBER_JSON}">json</a></b>, which wrapped <a href="{JHU_CSSE_REPO}">JHU CSSE</a>. That pipeline stopped updating on 2023-03-09.</p>
                    <p>* <b>USA States Source:</b> Bundled local snapshot of the NY Times state series from <a href="{NYT_COVID_REPO}">nytimes/covid-19-data</a> (<code>data/nytimes-us-states.csv</code>; original <b><a href="{NYT_US_STATES_CSV}">us-states.csv</a></b>), 2020-01-21 through 2023-03-23. NYT archived this dataset when daily reporting ended.</p>
                    <p>* <b>California Data Source (CURRENT):</b> Bundled local snapshot of the California county time series from <a href="{CHHS_CA_PAGE}">data.chhs.ca.gov</a> (<code>data/chhs-covid19cases-test.csv</code>; original <b><a href="{CHHS_CA_CSV}">csv</a></b>), 2020-02-01 through 2023-12-19. The old live download (and NY Times <b><a href="{NYT_US_COUNTIES_CSV}">us-counties.csv</a></b> fallback) is commented in <code>usa-ca/county-plot.py</code>.</p>
                    <p>* <b>California Data Source (DEPRECATED as of March 12, 2021):</b> The California county data was gathered from <a href="{CA_DATA_DEPRECATED_PAGE}">data.ca.gov</a>, they also provided a parseable <b><a href="{CA_DATA_DEPRECATED_CSV}">csv file</a></b> format.</p>
                    <p>* <b>Canada Data Source (CURRENT):</b> Bundled local snapshots of provincial/territorial cases and deaths from <a href="{CANADA_OPENCOVID}">COVID-19 Canada Open Data Working Group / CovidTimelineCanada</a> (<code>data/covidtimelinecanada-cases-pt.csv</code> and <code>data/covidtimelinecanada-deaths-pt.csv</code>; original <b><a href="{CANADA_CASES_CSV}">cases csv</a></b> and <b><a href="{CANADA_DEATHS_CSV}">deaths csv</a></b>, 2020 through 2023-12-31). Cases and deaths are outer-merged so every historical date from either file is kept.</p>
                    <p>* <b>Canada Data Source (DEPRECATED as of August 12, 2022):</b> The Canada data was gathered directly from <a href="{CANADA_DEPRECATED_REPO}">COVID-19 Canada Open Data Working Group</a> which generated a parsable <b><a href="{CANADA_DEPRECATED_CSV}">csv</a></b> daily. That source stopped getting updated in May of 2022.</p>
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

        # redundant (already in notes)

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

    # minify (htmlmin2 on Py3.13; skip minify if the package is missing)
    minihtml = htmlmin.minify(prettyhtml, remove_empty_space=True) if htmlmin else prettyhtml

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

# load the world time series as {country: [{date, confirmed, deaths, recovered}, ...]}
# plus per-country population and the OWID World series used for TOTAL
def load_world_owid():
    # Used to download live:
    # print(f"- Downloading world historical CSV from {SITE} (please wait)")
    # owid = read_csv_from_url(SITE, usecols=["country", "date", "total_cases", "total_deaths", "population", "continent"])
    # print(f"- Download Complete ({len(owid)} rows)")
    print(f"- Reading local world historical CSV from {OWID_LOCAL_CSV} (please wait)")
    print(f"- original online source was {SITE}")
    owid = read_csv_local(OWID_LOCAL_CSV, usecols=["country", "date", "total_cases", "total_deaths", "population", "continent"])
    print(f"- Local read complete ({len(owid)} rows)")

    owid["date"] = pd.to_datetime(owid["date"], errors="coerce")
    owid = owid.dropna(subset=["date", "country"])
    owid["date"] = owid["date"].dt.strftime("%Y-%m-%d")
    owid["total_cases"] = pd.to_numeric(owid["total_cases"], errors="coerce")
    owid["total_deaths"] = pd.to_numeric(owid["total_deaths"], errors="coerce")
    owid["population"] = pd.to_numeric(owid["population"], errors="coerce")

    # real places have a continent; keep World as the global total series
    is_world = owid["country"].eq("World")
    owid = owid[owid["continent"].notna() | is_world].copy()

    data = {}
    owid_pop = {}
    world_entries = None
    world_pop = None

    for country, group in owid.groupby("country", sort=True):
        group = group.sort_values("date")
        cases = group["total_cases"].ffill().fillna(0)
        deaths = group["total_deaths"].ffill().fillna(0)
        records = [
            {"date": d, "confirmed": int(c), "deaths": int(de), "recovered": 0}
            for d, c, de in zip(group["date"], cases, deaths)
        ]
        pop_series = group["population"].dropna()
        pop = int(pop_series.iloc[-1]) if len(pop_series) else None
        if int(cases.max()) <= 0 and int(deaths.max()) <= 0:
            continue
        if len(records) < 2:
            continue
        if country == "World":
            world_entries = records
            world_pop = pop
            continue
        data[country] = records
        owid_pop[country] = pop

    test_only = os.environ.get("COVID19_TEST_COUNTRIES", "").strip()
    if test_only:
        keep = {name.strip() for name in test_only.split(",") if name.strip()}
        data = {name: rows for name, rows in data.items() if name in keep}
        owid_pop = {name: owid_pop[name] for name in data}
        print(f"- COVID19_TEST_COUNTRIES set; plotting {sorted(data.keys())}")

    return data, owid_pop, world_entries, world_pop

def lookup_world_pop(pop_df, country_name):
    aliases = [country_name]
    if country_name in OWID_TO_WORLD_POP:
        aliases.append(OWID_TO_WORLD_POP[country_name])
    if country_name == "Korea, South":
        aliases.append("South Korea")
    for name in aliases:
        values = list(pop_df[pop_df["Country"] == name]["Population"].values)
        if len(values) > 0 and not math.isnan(values[0]):
            return int(values[0])
    return None

### main ###

def main():

    print("------------------------------")
    print(f"Covid19plot.py - v{Version}")
    print("------------------------------")
    print(f"- Plot theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize}")

    #### - GET DATA - METHOD 1 - START - ####
    # download OWID compact CSV and shape it like the old Pomber json
    if os.environ.get("COVID19_USE_TESTDATA"):
        print(f"- Loading json from {TESTDATA}. (please wait)")
        with open(TESTDATA) as f:
            data = json.load(f)
        owid_pop = {}
        world_entries = None
        world_pop = None
        print(f"- Loading Complete.")
    else:
        data, owid_pop, world_entries, world_pop = load_world_owid()
    if not data:
        print(f"- Download Failed (no data)")
        return
    #### - GET DATA - METHOD 1 - END - ####

    #### LOAD POPULATION DATA ####

    print(f"- Reading population csv from {POPFILE}")
    pop = pd.read_csv(POPFILE)

    #### PARSE BOTH DATA SETS POPULATION AND COVID ####

    list_of_countries=[]
    for x in data:
        str_country=x
        # prefer OWID population (matches the country names in the new source)
        curpop = owid_pop.get(str_country)
        if curpop == None:
            curpop = lookup_world_pop(pop, str_country)
        if curpop == None:
            print(f"* WARNING: Missing population data for {str_country=} {curpop=} in {POPFILE} file.")
        # work on covid data
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

    print(f"* {len(list_of_countries)} countries + 1 world total = {len(list_of_countries)+1} total plots")

    # world total: use OWID World when available (full historical global series)
    if world_entries:
        print("- Using OWID World series for TOTAL (full historical global cases/deaths)")
        oldEntry=None
        total_entry_list=[]
        for i in world_entries:
            entry=Entry(i["date"], i["confirmed"], i["deaths"], i["recovered"], prevEntry=oldEntry)
            oldEntry=entry
            total_entry_list.append(entry)
        if world_pop == None:
            world_pop = int(list(pop[pop["Country"] == "Earth"]["Population"].values)[0])
        total_country=Country("TOTAL",total_entry_list,population=world_pop)
        list_of_countries.append(total_country)
    else:
        # fallback: sum every country per date (old Pomber/test-json path)
        all_dates=[]
        for i in list_of_countries:
            if len(i.date_list) > len(all_dates):
                all_dates=i.date_list
        i=0
        oldEntry=None
        total_entry_list=[]
        for d in all_dates:
            total_confirmed=0
            total_deaths=0
            total_recovered=0
            for i in list_of_countries:
                for e in i.entrylist:
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
