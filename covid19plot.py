import json
import urllib.request
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline.offline
# import plotly.plotly as py
import string
import os
import datetime
import bs4
import htmlmin
import numpy as np
from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures
import pickle
from scipy.optimize import curve_fit
from os import path

# By: Kostia Khlebopros
# Site: http://www.infotinks.com/coronavirus-dashboard-covid19-py/
# Github: https://github.com/bhbmaster/covid19

### constants ###

VersionFile = "VERSION"  # Last Update YY.MM.DD
Version = open(VersionFile,"r").readline().rstrip().lstrip() if path.exists(VersionFile) else "NA"
SITE="https://pomber.github.io/covid19/timeseries.json"
start_time = datetime.datetime.now()
start_time_string = start_time.strftime("%Y-%m-%d %H:%M:%S")
start_time_posix = start_time.strftime("%Y-%m-%d-%H-%M-%S")
bootstrapped = False
sigdigit=5
sigdigit_small=2
predict_days_min=5
predict_days_max=15
valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
TESTDATA = "code/CountryTestData.json"
moving_average_samples = 7 # 7 day moving average for daily new cases and daily deaths
days_predict_new_cases = 30
ThemeFile = "PLOTLY_THEME" # contents are comma sep: theme,font family,font size

# get theme stuff from file
ThemeFileContents = open(ThemeFile,"r").readline().rstrip().lstrip().split(",")
Theme_Template = ThemeFileContents[0] if path.exists(ThemeFile) else "none"
Theme_Font = ThemeFileContents[1] if path.exists(ThemeFile) else "Arial"
Theme_FontSize = int(ThemeFileContents[2]) if path.exists(ThemeFile) else 12

### classes ###

# a single entry class
class Entry:
    def __init__(self,date,cases,deaths,recovered,prevEntry=None):
        self.date=date
        if cases == None:
            cases=0
        if deaths == None:
            deaths=0
        if recovered == None:
            recovered=0
        if cases < 0:
            cases = 0
        if deaths < 0:
            deaths = 0
        if recovered < 0:
            recovered = 0
        self.cases=cases
        self.deaths=deaths
        self.recovered=recovered
        # print(f"{date}, {cases}, {deaths}, {recovered}.")
        self.active=cases-deaths-recovered
        # death & recovery %
        if cases == 0:
            self.death_percent=None
            self.recovery_percent=None
        else:
            self.death_percent=(self.deaths/self.cases)*100.0
            self.recovery_percent=(self.recovered/self.cases)*100.0
        if prevEntry:
            self.delta_cases=cases-prevEntry.cases
            self.delta_active=self.active-prevEntry.active
            self.delta_recovered=self.recovered-prevEntry.recovered
            self.delta_deaths=self.deaths-prevEntry.deaths
            # ratio cases
            try:
                self.delta_ratio_cases=cases/prevEntry.cases
            except:
                self.delta_ratio_cases=None
            # ratio active cases
            try:
                self.delta_ratio_active=self.active/prevEntry.active
            except:
                self.delta_ratio_active=None
            # ratio recovered
            try:
                self.delta_ratio_recovered=self.recovered/prevEntry.recovered
            except:
                self.delta_ratio_recovered=None
            # ratio deaths
            try:
                self.delta_ratio_deaths=self.deaths/prevEntry.deaths
            except:
                self.delta_ratio_deaths=None
        else:
            self.delta_cases=0 # hack more info below
            self.delta_active=None
            self.delta_recovered=None
            self.delta_deaths=0 # hack more info below
            self.delta_ratio_cases=None
            self.delta_ratio_active=None
            self.delta_ratio_recovered=None
            self.delta_ratio_deaths=None
            # hack: used to be None but that fails average calc in moving average (as you can't sum None+ints like None+3+2). Perhaps its better to delete the entry (so the date|x and value|y are just gone. The plots should still work with those missing points).

# a country class, full of entries
class Country:
    def __init__(self,country,entrylist):
        self.country=country
        self.countryposix=''.join(c for c in self.country if c in valid_chars)
        self.entrylist=entrylist
        self.date_list=[]
        self.cases_list=[]
        self.deaths_list=[]
        self.recovered_list=[]
        self.active_list=[]
        # cases
        self.delta_cases_list=[]
        self.delta_ratio_cases_list=[]
        # active
        self.delta_active_list=[]
        self.delta_ratio_active_list=[]
        # recovered
        self.delta_recovered_list=[]
        self.delta_ratio_recovered_list=[]
        # deaths
        self.delta_deaths_list=[]
        self.delta_ratio_deaths_list=[]
        # death + recovery %
        self.death_percent_list=[]
        self.recovery_percent_list=[]
        for i in entrylist:
            self.date_list.append(i.date)
            self.cases_list.append(i.cases)
            self.deaths_list.append(i.deaths)
            self.recovered_list.append(i.recovered)
            self.active_list.append(i.active)
            self.delta_cases_list.append(i.delta_cases)
            self.delta_ratio_cases_list.append(i.delta_ratio_cases)
            self.delta_active_list.append(i.delta_active)
            self.delta_ratio_active_list.append(i.delta_ratio_active)
            self.delta_recovered_list.append(i.delta_recovered)
            self.delta_ratio_recovered_list.append(i.delta_ratio_recovered)
            self.delta_deaths_list.append(i.delta_deaths)
            self.delta_ratio_deaths_list.append(i.delta_ratio_deaths)
            # death + recovery %
            self.death_percent_list.append(i.death_percent)
            self.recovery_percent_list.append(i.recovery_percent)
        self.length=len(entrylist)
        lasti=self.length-1
        self.last_date=entrylist[lasti].date
        self.last_cases=entrylist[lasti].cases
        self.last_deaths=entrylist[lasti].deaths
        self.last_recovered=entrylist[lasti].recovered
        self.last_active=entrylist[lasti].active
        self.last_delta_cases = entrylist[lasti].delta_cases
        self.last_delta_active = entrylist[lasti].delta_active
        self.last_delta_recovered = entrylist[lasti].delta_recovered
        self.last_delta_deaths = entrylist[lasti].delta_deaths
        self.last_delta_ratio_cases = entrylist[lasti].delta_ratio_cases
        self.last_delta_ratio_active = entrylist[lasti].delta_ratio_active
        self.last_delta_ratio_recovered = entrylist[lasti].delta_ratio_recovered
        self.last_delta_ratio_deaths = entrylist[lasti].delta_ratio_deaths
        # death + recovery %
        self.last_death_percent = entrylist[lasti].death_percent
        self.last_recovery_percent = entrylist[lasti].recovery_percent
        # prediction of when we get 0 daily new cases (this is calculated later; but i guess if we refactor can bring it into this class)
        self.predict_date_zero = None # calculated and set in graph2div, called from there and div2html

    # input list type, output x (date list) and y (values) and r^2 and m and b0. uses last X days to predict
    def lastXdayslinearpredict(self, list, days=10):
        success=True
        try:
            # grab last 10 days or whatever
            days=int(days)
            x0=self.date_list[-(days+1):-1]
            y0=list[-(days+1):-1]
            # get first day
            day0=x0[0]
            # new days 0 thru 10
            x00=[]
            for i in range(len(x0)):
                x00.append(i)
            # now should have
            # x00=0,1,2,3,4,5,6,7,8,9
            # y0=with ten values
            # linear fit
            x = np.array(x00).reshape((-1, 1))
            y = np.array(y0)
            model = LinearRegression()
            model.fit(x, y)
            r_sq = model.score(x, y)
            b0=model.intercept_
            m=float(model.coef_)
            # print('* day 0:', day0)
            # print('* coefficient of determination:', r_sq)
            # print('* intercept:', b0)
            # print('* slope:', m)
            xpred0=[]
            for i in range(len(x0)*2):
                xpred0.append(i)
            xpred=np.array(xpred0).reshape((-1,1))
            y_pred = model.predict(xpred)
            # print('predicted response:', y_pred, sep='\n')
            # convert day 0,1,2,3,4 to day0+day
            day0dt=datetime.datetime.strptime(day0, "%Y-%m-%d")
            xdays=[]
            for i in xpred0:
                newdt=day0dt+datetime.timedelta(days=int(i))  # add x number of days
                newday=newdt.strftime("%Y-%m-%d")
                xdays.append(newday)
            # final answer
            xfinal=xdays   # need to convert these to dates of same format yyyy-mm-dd
            yfinal=y_pred.tolist()
        except:
            success=False
            xfinal=None
            yfinal=None
            r_sq=None
            m=None
            b0=None
        return (success,xfinal,yfinal,r_sq,m,b0)

    # input list type. uses last X days to predict - fit to a/(x+c) + b
    def lastXdayscurvefit(self, list, days=10):
        success=True
        try:
            # grab last 10 days or whatever
            days=int(days)
            x0=self.date_list[-(days+1):-1]
            y0=list[-(days+1):-1]
            # get first day
            day0=x0[0]
            # new days 0 thru 10
            x00=[]
            for i in range(len(x0)):
                x00.append(i)
            # now should have
            # x00=0,1,2,3,4,5,6,7,8,9
            # y0=with ten values
            # linear fit
            x = np.array(x00).reshape((-1, 1))
            y = np.array(y0)
            # print("DEBUG:",x,y)
            fit_func = lambda x,a,b,c: a*x**2 + b*x +c # polynomial
            # fit_func = lambda x,a,b,c: a/(x+c)+b # the curve function
            model = curve_fit(fit_func,np.array(x00),np.array(y0))
            # get parms from the fit
            [ a, b, c ] = model[0]
            # print(f"DEBUGED: a={a} b={b} c={c}")
            xpred0=[]
            for i in range(len(x0)*2): # how far out we predict (as many days forward as we looked back)
                xpred0.append(i)
            xpred = np.array(xpred0).reshape((-1,1))  # verticle xs
            y_pred = np.array(fit_func(xpred,a,b,c))
            # print('predicted response:', y_pred, sep='\n')
            # convert day 0,1,2,3,4 to day0+day
            day0dt=datetime.datetime.strptime(day0, "%Y-%m-%d")
            xdays=[]
            for i in xpred0:
                newdt=day0dt+datetime.timedelta(days=int(i))  # add x number of days
                newday=newdt.strftime("%Y-%m-%d")
                xdays.append(newday)
            # final answer
            xfinal=xdays   # need to convert these to dates of same format yyyy-mm-dd
            yfinal=[ float(i[0]) for i in y_pred.tolist() ]
        except Exception as e:
            # print("CURVE FIT ERROR:",e)
            success=False
            xfinal=None
            yfinal=None
            a=None
            b=None
            c=None
        return (success,xfinal,yfinal,a,b,c)

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

# N day moving average (ex: 7 day average). averages the y values over window size N, our array shrinks by N-1 due to this. therefore, we also truncate the x array values by N-1 from the left side (older dates are on the left side)
def avgN(N,x,y):
    # example:
    # y = [1, 2, 3, 7, 9]  # numbers
    # N = 3                # window_size
    # output is [2.0, 4.0, 6.333333333333333]
    # *** get y values - moving average algo
    mov_y = []
    # print("DEBUG:",y)
    for i in range(len(y) - N + 1):
        wind = y[i : i + N]
        wind_avg = sum(wind) / N
        mov_y.append(wind_avg)
    # *** get x values - truncates N-1 number from begin
    mov_x = x[N-1:]
    # *** return tuple
    return (mov_x,mov_y)

# create divs of graph of a certain type from country class item

def graph2div(country_class,graph_type):

    i=country_class

    if graph_type=="log":           # log
        the_type_string="LOG"
        the_type_string_camel="Log"
        the_type_fig="log"
    else:                           # normal
        the_type_string="NORMAL"
        the_type_string_camel="Normal"
        the_type_fig=None

    country_name=i.country
    full_path_html=f"html-plots/{i.countryposix}-plot-{the_type_string}.html"

    subplot_titles = (f"Cases, Deaths, Recovered, Active",f"Death & Recovery %",
    f"Ratio Diff of Cases, Deaths, Active",f"Ratio Diff of Active",
    f"Daily Cases",f"Daily Deaths")
    spacing = 0.035

    fig = make_subplots(rows=2, cols=2, horizontal_spacing=spacing, vertical_spacing=spacing, subplot_titles=subplot_titles,shared_xaxes=True) # used to be make_subplots(rows=2, cols=2), then made it (3,2) ,then  middle row back to (2,2)

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
        "hovermode": 'x unified',
        "template": Theme_Template
    }

    # Note: instead of Diff it used to say Δ, but that renders weird on html (I tried to fix it but too much work for something small)

    fig.update_layout(title=f"<b>{country_name} - Covid19 {the_type_string_camel} Plots</b> - covid19plot.py v{Version}<br><b>Last Data Point:</b> {i.last_date} , <b>Updated On:</b> {start_time_string}",**plot_options)

    fig.add_trace(go.Scatter(x=i.date_list, y=i.cases_list, name=f"<b>Cases</b> : y<sub>fin</sub>={round_or_none(i.cases_list[-1],0)}", line=dict(color='firebrick', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=i.deaths_list, name=f"<b>Deaths</b> : y<sub>fin</sub>={round_or_none(i.deaths_list[-1],0)}", line=dict(color='red', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=i.recovered_list, name=f"<b>Recovered</b> : y<sub>fin</sub>={round_or_none(i.recovered_list[-1],0)}", line=dict(color='green', width=2),showlegend=True),row=1,col=1)

    fig.add_trace(go.Scatter(x=i.date_list, y=i.active_list, name=f"<b>Active Cases</b> : y<sub>fin</sub>={round_or_none(i.active_list[-1],0)}", line=dict(color='purple', width=2),showlegend=True),row=1,col=1)

    ## OLD-MIDDLE-ROW ## fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_cases_list, name=f"<b>Ratio Diff Cases</b> : y<sub>fin</sub>={round_or_none(i.delta_ratio_cases_list[1],5)}", showlegend=True),row=2,col=1)

    # fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_active_list, name="<b>Ratio Diff Active Cases</b>", showlegend=True),row=2,col=1)

    # fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_recovered_list, name="Ratio Diff Recovered", showlegend=True),row=2,col=1)

    ## OLD-MIDDLE-ROW ## fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_deaths_list, name=f"<b>Ratio Diff Deaths</b> : y<sub>fin</sub>={round_or_none(i.delta_ratio_deaths_list[-1],5)}", showlegend=True),row=2,col=1)

    ## OLD-MIDDLE-ROW ## fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_active_list, name=f"<b>Ratio Diff Active Cases</b> : y<sub>fin</sub>={round_or_none(i.delta_ratio_active_list[-1],5)}", showlegend=True),row=2,col=2)

    ## OLD-MIDDLE-ROW ## ### # ~~~ ratio prediction - start ~~~ #
    ### for ds in range(predict_days_min,predict_days_max+1):
    ###     success, xfinal, yfinal, r_sq, m, b0 = i.lastXdayslinearpredict(i.delta_ratio_active_list, ds)
    ###     if success:
    ###         # fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"Past {ds} day Linear Regression Fit (r^2={r_sq})", line=dict(color='gray', width=1), showlegend=True), row=2,col=2)
    ###         fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"Past {ds} day Linear Regression Fit (r^2={round(r_sq,sigdigit)})", line=dict(width=1), showlegend=True), row=2,col=2)
    ### # ~~~ ratio prediction - end ~~~ #

    # ~~~ start new plot ~~~ #

    fig.add_trace(go.Scatter(x=i.date_list, y=i.death_percent_list, name=f"<b>Death %</b> : y<sub>fin</sub>={round_or_none(i.death_percent_list[-1],2)}%", showlegend=True),row=1,col=2)

    fig.add_trace(go.Scatter(x=i.date_list, y=i.recovery_percent_list, name=f"<b>Recovery %</b> : y<sub>fin</sub>={round_or_none(i.recovery_percent_list[-1],2)}%", showlegend=True),row=1,col=2)

    # fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_active_list, name="Delta Active Cases", showlegend=True),row=1,col=2) # doesn't show negative so not including

    # ~~~ end new plot ~~~ #

    # ~~~ start new plot ~~~ #

    # ... daily new cases ... #

    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_cases_list, name=f"<b>New Cases</b> : y<sub>fin</sub>={round_or_none(i.delta_cases_list[-1],0)}", showlegend=True),row=2,col=1) # when had OLD-MIDDLE-ROW this was row=3,col=1

    xavg,yavg = avgN(moving_average_samples,i.date_list,i.delta_cases_list)

    fig.add_trace(go.Scatter(x=xavg, y=yavg, name=f"<b>New Cases {moving_average_samples}day Moving Avg</b> : y<sub>fin</sub>={round_or_none(yavg[-1],0)}", showlegend=True),row=2,col=1) # when had OLD-MIDDLE-ROW this was row=3,col=1

    ## success,xfinal,yfinal,fita,fitb,fitc = i.lastXdayscurvefit(yavg,days_predict_new_cases)

    success, xfinal, yfinal, r_sq, m, b0 = i.lastXdayslinearpredict(yavg, days_predict_new_cases)

    # print(f"DEBUG: fit -> success={success} fita={fita} fitb={fitb} fitc={fitc}")
    # print(f"DEBUG: fit -> xfinal={xfinal} yfinal={yfinal}")

    if success:

        # predict when cross y=0

        if m != 0: # don't calc crossing if slope is 0 or flat, as its not existant

            y_to_cross = 0.0 # target y to cross (find which X equals at the Y value)
            x_cross1 = (y_to_cross - float(b0)) / float(m)   # y=mx+b   ->   x=(y-b)/m
            x_cross1_int=int(x_cross1)  # convert to int value (as we need 1 day or 3 day from day0 type of thing)
            day0=xfinal[0]  # this is x0 essentially and its a date
            day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")  # convert to date time date so we can add x_cross to it
            daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))  # get the date when we cross by adding x_cross to day0
            daycross = daycrossdt.strftime("%Y-%m-%d")  # convert to easy to understand text

        else:

            daycross = None

        i.predict_date_zero = daycross  # this variable doesn't exist in Country class, but in python you can create it regardless (we call it later when creating the HTML)

        ## fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"Daily New Cases Prediction Curve Fit (y={fita:.3f}x^2+{fitb:.3f}x+{fitc:.0f})", line=dict(color='gray', width=2), showlegend=True), row=3,col=1)

        fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"<b>Daily New Cases {days_predict_new_cases} Days Prediction</b><br>r<sup>2</sup>={r_sq:0.5f}<br>y={m:0.3f}x+{b0:0.1f} where x<sub>0</sub>={xfinal[0]}<br>y=0 / no new cases predicted @ {daycross}", line=dict(color='black', width=1, dash='dash'), showlegend=True), row=2,col=1) # when had OLD-MIDDLE-ROW this was row=3,col=1

        # half_index = int(len(xfinal)/2)
        # # text for the fit
        # text_string=f"y={m:0.2f}x+{b0:0.0f} (r^2={r_sq:0.5f})"
        # color_text="purple"
        # fig.add_annotation(x=xfinal[half_index], y=yfinal[half_index],
        #     text=text_string,
        #     showarrow=True,
        #     font=dict(
        #         family="courier",
        #         size=12,
        #         color=color_text
        #     ),
        #     arrowhead=1, arrowsize=2, arrowcolor=color_text, arrowwidth=1, row=3,col=1)

    # ...  daily deaths ... #

    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_deaths_list, name=f"<b>New Deaths</b> : y<sub>fin</sub>={round_or_none(i.delta_deaths_list[-1],0)}", showlegend=True),row=2,col=2) # when had OLD-MIDDLE-ROW this was row=3,col=1

    xavg,yavg = avgN(moving_average_samples,i.date_list,i.delta_deaths_list)

    fig.add_trace(go.Scatter(x=xavg, y=yavg, name=f"<b>New Deaths {moving_average_samples}day Moving Avg</b> : y<sub>fin</sub>={round_or_none(yavg[-1],0)}", showlegend=True),row=2,col=2) # when had OLD-MIDDLE-ROW this was row=3,col=1

    # ~~~ end new plot ~~~ #

    fig.update_yaxes(type=the_type_fig,row=1,col=1)

    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=1)

    fig.update_yaxes(type=None,row=1,col=2) # new plot

    # fig.update_yaxes(type="log",row=1,col=2) # new plot

    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=2) # new plot

    fig.write_html(full_path_html,auto_open=False) # write 2.5 MiB html file

    div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')

    return div

# create html file out of div list

def divs2html(div_list,type_title,time_string,output_file,bootstrap_on=False):

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
        <title>Covid19Plot.py Plots {type_title} Scale</title>
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
        </style>
    <head/>
    <body>
        <h2 class="roundback bigger"><u>Covid19Plot.py Country {type_title} Plots</u> - v{Version}</h2>
        <p><b>Last Data Point:</b> {last_date} , <b>Updated On:</b> {time_string}</p>
        <p>* <b>Caution - Page might take a long moment to load: </b> this is a large HTML file (over 20 MiB). The loading progress percentage is at top right corner; it might hover around 99%, please be patient as it will finish. If the progress percentage not shown, just wait for browser to awknowledge the page is done loading.</p>
        <p>* <b>Other Plots:</b></p>
        <p>- <a href='covid19-{other_type_title.lower()}.html'>Click here to see <b>Covid19Plot.py Country {other_type_title} Plots</b>.</a></p>
        <p>- <a href='usa-ca/county-output.html'>Click here to see <b>California's Counties Daily New Cases Plots</b>.</a></p>
        <p>* <b>How To Use:</b> Scroll down to the country of inquiry via "Quick Navigation" or scroll manually. To get an interactive plot open the "Normal" or "Log" link - which opens the countries plot seperately, the plots are fully interactive when displayed seperately. The different lines / traces can enabled, disabled, all-enabled ,or one-enabled by clicking and double clicking on the legend items. The California county plots are also similarly interactive.</p>
        <p>* <b>Source Code & Other Links:</b> available on <a href="https://github.com/bhbmaster/covid19">GitHub</a> and <a href="http://www.infotinks.com/coronavirus-dashboard-covid19-py/">infotinks.com</a></p>
        <p>* <b>Diff Change</b> or <b>Delta</b> is change from previous day ( + is growth; - is reduction )</p>
        <p>* <b>Ratio Diff Change</b> or <b>Ratio</b> is % change from previous day ( 1 or higher is growth; 0 to 1 is reduction )</p>
        <p>* <b>Note:</b> Each countries covid stats and plots are shown one by one. Countries are sorted by total cases in increasing order, so the country in #1 is the leader in most covid cases to date.</p>
        <p>* <b>Note:</b> The very first 'country' to be shown is actually not a country but the world total represented as "TOTAL". It will always have the highest number of cases, as its the sum of all countries, so its takes spot #0 at the very top.
        <p>* <b>Note:</b> Peak active case prediction date is calculated using a linear regression fit on "active cases ratio" and examing its past X days values to see when it crosses 1.0.</p>
        <p>* An r<sup>2</sup> closer to 1.0 means a better prediction.</p>
        <p>* Ignore predictions with past dates.</p>
        <p>* <b>Note:</b> Daily new cases moving average has a linear regression fit calculated from previous {days_predict_new_cases} days and extending same days into the future. This is to help estimate daily new cases trend. Of course, the real trend is not linear, so this is strictly a prediction. The predicted line has its r<sup>2</sup> fit value and y=mx+b equation shown in the legend. x is number of days since x<sub>0</sub>, which is provided in the label. y is predicted daily new cases (technically its the predicted moving average of the daily new cases). Finally, we predict the day we reach 0 daily new cases; also shown on the legend.</p>
        <p>* <b>Note:</b> The plotly graphs are interactive. To have better you can click on the "Normal" or "Log" link for each country to see it's own interactive plot.</p>
        <p>There you can control control which information is plotted by clicking & double clicking on the items in the legend to isolate or disable that data.</p>
        <p>* <b>Note:</b> Active Cases is calculated by subtracting Recovered and Deaths from total Cases.</p>
        <p>* <b>Note:</b> The United States, US, recovery numbers are all nullfied to 0 on 2020-12-15 and onward. This was a decision made by the data source. More can be read here: <a href="https://github.com/CSSEGISandData/COVID-19/issues/3464">Github Issue</a> and <a href="https://covidtracking.com/about-data/faq#why-have-you-stopped-reporting-national-recoveries">Reasoning</a>.</p>
        <p>* <b>World Data Source:</b> The world data is gathered directly from <a href="https://pomber.github.io/covid19/">Pomber</a> which generates a parsable <b><a href="{SITE}">json</a></b> daily. They use the data from <a href="https://github.com/CSSEGISandData/COVID-19">CSSEGISandData</a> data to generate that json.</p>
        <p>* <b>California Data Source (CURRENT DATA - covers from 2020-01-01 to now):</b> The California county data is gathered from <a href="https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state">data.chhs.ca.gov</a>, they also provide a parseable <b><a href="https://data.chhs.ca.gov/dataset/f333528b-4d38-4814-bebb-12db1f10f535/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a/download/covid19cases_test.csv">csv file</a></b> format.</p>
        <p>* <b>California Data Source (DEPRECATED AS OF MARCH 12 2021):</b> The California county data is gathered from <a href="https://data.ca.gov/dataset/covid-19-cases/resource/926fd08f-cc91-4828-af38-bd45de97f8c3">data.ca.gov</a>, they also provide a parseable <b><a href="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv">csv file</a></b> format.</p>
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

    for country,div in div_list:

        place_num += 1

        # cases
        try:
            ldr_cases=round(country.last_delta_ratio_cases,sigdigit)
        except:
            ldr_cases=country.last_delta_ratio_cases

        # deaths
        try:
            ldr_deaths=round(country.last_delta_ratio_deaths,sigdigit)
        except:
            ldr_deaths=country.last_delta_ratio_deaths

        # recovered
        try:
            ldr_recovered=round(country.last_delta_ratio_recovered,sigdigit)
        except:
            ldr_recovered=country.last_delta_ratio_recovered

        # active
        try:
            ldr_active=round(country.last_delta_ratio_active,sigdigit)
        except:
            ldr_active=country.last_delta_ratio_active

        # type_title comes in as Log (doesn't work) turns to LOG (works), comes in as Normal (doesn't work )turns to NORMAL (works)
        # html += f"        <h3><a href='html-plots/{country.countryposix}-plot-{type_title.upper()}.html'>{country.country}</a></h3>\n"

        html += f"<a id='{country.countryposix}'></a><h3 class='roundback'><u>#{place_num}. {country.country}</u> - <a href='#search_anchor'>Back To Search / Top</a></h3>\n"

        html += f"<p><a href='html-plots/{country.countryposix}-plot-NORMAL.html'>Normal</a> | <a href='html-plots/{country.countryposix}-plot-LOG.html'>Log</a></p>"

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
        <td>{country.last_cases}</td>
        <td>{country.last_delta_cases}</td>
        <td>{ldr_cases}</td>
        </tr>
        <tr>
        <td>Deaths</td>
        <td>{country.last_deaths}</td>
        <td>{country.last_delta_deaths}</td>
        <td>{ldr_deaths}</td>
        </tr>
        <tr>
        <td>Recovered</td>
        <td>{country.last_recovered}</td>
        <td>{country.last_delta_recovered}</td>
        <td>{ldr_recovered}</td>
        </tr>
        <tr>
        <td>Active Cases</td>
        <td>{country.last_active}</td>
        <td>{country.last_delta_active}</td>
        <td>{ldr_active}</td>
        </tr>
        </tbody>
        </table>\n"""

        # death & recovery percent

        # deaths %
        try:
            lp_deaths=round(country.last_death_percent,sigdigit_small)
        except:
            lp_deaths=country.last_death_percent

        # recovery %
        try:
            lp_recovered=round(country.last_recovery_percent,sigdigit_small)
        except:
            lp_recovered=country.last_recovery_percent

        html += f"""<p>* Last percent <b>recovered</b> from all cases: <b>{lp_recovered}%</b></p>
        <p>* Last percent <b>dead</b> from all cases: <b>{lp_deaths}%</b></p>\n"""

        #  ~~~ below - active new cases prediction ~~~ #

        html += f"<p>* Predict <b>0 New Daily Cases</b> date</b> using {days_predict_new_cases} day linear regression: <b>{country.predict_date_zero}</b></p>"

        # ~~~ above - active new cases prediction ~~~ #

        # ~~~ below - ratio prediction ~~~ #

        predict_list=[]

        for pdays in range(predict_days_min,predict_days_max+1):

            success, xfinal, yfinal, r_sq, m, b0 = country.lastXdayslinearpredict(country.delta_ratio_active_list, pdays)

            if success:

                try:
                    x_cross1 = (1.0 - float(b0)) / float(m)
                    x_cross1_int=int(x_cross1)
                    day0=xfinal[0]
                    day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")
                    daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))
                    daycross = daycrossdt.strftime("%Y-%m-%d")
                    # html += f"<p>* Using past {pdays} days for prediction, Active Cases might peak on {daycross}. The r^2 for this fit is {round(r_sq,sigdigit)}</p>\n"
                except:
                    success=False
                    daycross=None
                    r_sq=None

            predict_item=[pdays,success,daycross,None if r_sq == None else round(r_sq,sigdigit)]

            predict_list.append(predict_item)

        html += """<p><b>Active Case Peak Prediction</b>: using past X days of "active case ratio" in a linear regression fit algorithm</p>
        <table border="1" cellpadding="5">
        <tbody>
        <tr>
        <td>past days</td>\n"""

        for a in predict_list:
            html += f"<td>{a[0]}</td>\n"

        html += """</tr>
        <tr>
        <td>predicted peak date</td>\n"""

        for a in predict_list:
            html += f"<td>{a[2]}</td>\n"

        html += """</tr>
        <tr>
        <td>r<sup>2</sup></td>\n"""

        for a in predict_list:
            html += f"<td>{a[3]}</td>\n"

        html += """</tr>
        </tbody>
        </table>\n"""

        # ~~~ above prediction ~~~ #

        html += "        " + div+"\n"

        # redundant (already in notes # html += '<p>* <b>Note:</b> Data Source: <a href="https://pomber.github.io/covid19/">Pomber</a>, which generates daily json from <a href="https://github.com/CSSEGISandData/COVID-19">CSSEGISandData</a> data.</p>\n'
 
    html += f"""<!-- hitwebcounter Code START -->
    <a href="https://www.hitwebcounter.com" target="_blank">
    <img src="{countersite}" title="Views:" Alt="hitwebcounter" border="0" >
    </a>
    </body>"""
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
    </html>"""

    # ~~~ end of html ~~~ #

    # make it pretty
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
    	print(f"- Download Failed (no data).")
    print(f"- Download Complete.")
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

    # last_date=data["China"][len(data["China"])-1]["date"]  # returns 2020-3-14

    # last_confirmed=0
    # last_deaths=0
    # last_recovered=0
    # last_active = 0

    list_of_countries=[]
    for x in data:
        str_country=x
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
            # if i["date"] == last_date:
            #     today=i
            #     confirmed=i["confirmed"]
            #     deaths=i["deaths"]
            #     recovered=i["recovered"]
            #     active=confirmed-deaths-recovered
            #     last_confirmed+=confirmed
            #     last_deaths+=deaths
            #     last_recovered+=recovered
            #     last_active+=active
        country=Country(str_country,list_of_entries)
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

    #### - DEBUG TEST DATA - START ####
    # # For quicker runs - for tests: only work with China, US and Canada by creating new list only w/ those countries
    # TestCountries = [ "China", "US", "Canada" ]
    # test_list_of_countries = []
    # print(f"* {len(TestCountries)} countries + 1 world total = {len(TestCountries)+1} total plots (modified for debug / testing)")
    # for i in list_of_countries:
    #     if i.country in TestCountries:
    #         test_list_of_countries.append(i)
    # list_of_countries = test_list_of_countries
    #### - DEBUG TEST DATA - END ####

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
    total_country=Country("TOTAL",total_entry_list)
    list_of_countries.append(total_country)

    # sort list of countries by total cases (TOTAL will be at top)
    list_of_countries.sort(key=lambda x: x.last_cases, reverse=True)

    # # test linear
    # print("======")
    # test_country=list_of_countries[1]
    # print(f"- country = {test_country.country}")
    # xfinal,yfinal,r_sq,m,b0 = test_country.lastXdayslinearpredict(test_country.delta_ratio_active_list,10)
    # print(f"- xfinal = {xfinal}")
    # print(f"- yfinal = {yfinal}")
    # print(f"- r^2 = {r_sq} || y={m}x+{b0}")
    # x_cross1=(1.0-b0)/m
    # print(f"- predict cross 1 @ {x_cross1}")
    # print("======")

    # plot all

    rows=len(list_of_countries)
    n=1
    div_list_log=[]
    div_list_normal=[]
    if not os.path.exists("html-plots"):
        os.mkdir("html-plots")
    if not os.path.exists("img-plots"):
        os.mkdir("img-plots")

    # create divs for each country and store in lists

    for i in list_of_countries:
        # normal
        div=graph2div(i,"normal")
        div_list_normal.append((i,div))
        # log
        div=graph2div(i,"log")
        div_list_log.append((i,div))
        # done creating div plots message
        print(f"{n}/{rows} - {i.country} - last value from {i.last_date} with {i.last_cases} cases, {i.last_deaths} deaths, {i.last_recovered} recovered, {i.last_active} active cases.")
        n+=1

    # create the html

    # create html from div list - normal
    print("Creating 'covid19-normal.html', please wait.")
    divs2html(div_list_normal,"Normal",start_time_string,"covid19-normal.html",bootstrapped)

    # create html from div list - log
    print("Creating 'covid19-log.html', please wait.")
    divs2html(div_list_log,"Log",start_time_string,"covid19-log.html",bootstrapped)

    # save 
    # save_pickle(list_of_countries,"country-class-list",start_time_posix)

    # complete message
    print("Generating plots & html done!")

if __name__ == "__main__":
    main()

### the end ###
