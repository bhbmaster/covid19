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

# By: Kostia Khlebopros
# Site: http://www.infotinks.com/coronavirus-dashboard-covid19-py/
# Github: https://github.com/bhbmaster/covid19
# Last Update: 2021-02-19

### constants ###

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
            self.delta_cases=None
            self.delta_active=None
            self.delta_recovered=None
            self.delta_deaths=None
            self.delta_ratio_cases=None
            self.delta_ratio_active=None
            self.delta_ratio_recovered=None
            self.delta_ratio_deaths=None

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

### functions ###

# create divs of graph of a certain type from country class item

def graph2div(country_class,graph_type):
    i=country_class
    if graph_type=="log":           # log
        the_type_string="LOG"
        the_type_fig="log"
    else:                           # normal
        the_type_string="NORMAL"
        the_type_fig=None
    country_name=i.country
    full_path_html=f"html-plots/{i.countryposix}-plot-{the_type_string}.html"
    fig = make_subplots(rows=2, cols=2)
    fig.update_layout(title=f"COVID19 - {country_name}")
    fig.add_trace(go.Scatter(x=i.date_list, y=i.cases_list, name="Cases", line=dict(color='firebrick', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.deaths_list, name="Deaths", line=dict(color='red', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.recovered_list, name="Recovered", line=dict(color='green', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.active_list, name="Active Cases (Cases - Deaths & Recovered)", line=dict(color='purple', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_cases_list, name="Ratio Diff Cases", showlegend=True),row=2,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_active_list, name="Ratio Diff Active Cases", showlegend=True),row=2,col=1)
    #fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_recovered_list, name="Ratio Diff Recovered", showlegend=True),row=2,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_deaths_list, name="Ratio Diff Deaths", showlegend=True),row=2,col=1)
    # below - ratio prediction
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_active_list, name="Ratio Diff Active Cases", showlegend=True),row=2,col=2)
    for ds in range(predict_days_min,predict_days_max+1):
        success, xfinal, yfinal, r_sq, m, b0 = i.lastXdayslinearpredict(i.delta_ratio_active_list, ds)
        if success:
            # fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"Past {ds} day Linear Regression Fit (r^2={r_sq})", line=dict(color='gray', width=1), showlegend=True), row=2,col=2)
            fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=f"Past {ds} day Linear Regression Fit (r^2={round(r_sq,sigdigit)})", line=dict(width=1), showlegend=True), row=2,col=2)
    # above  - ratio prediction
    # new plot
    fig.add_trace(go.Scatter(x=i.date_list, y=i.death_percent_list, name="Death %", showlegend=True),row=1,col=2)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.recovery_percent_list, name="Recovery %", showlegend=True),row=1,col=2)
    # fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_active_list, name="Delta Active Cases", showlegend=True),row=1,col=2) # doesnt show negative so not including
    # end new plot
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
    # start of html
    # html = """<!DOCTYPE html>                # with html5 the divs are 50% height, without this they are 100%
    html = f"""<html>
    <head>
        <title>Covid19.py Plots {type_title} Scale</title>
        {bootstrap_string}
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
	        h2, h3, p, table {{
	            margin-left: 40px;
	        }}
	        div {{
	            height: 100%;
	        }}
            td {{
                text-align: center;
            }}
	    </style>
    <head/>
    <body>
        <h2>Covid19.py Plots ({type_title})</h2>
        <p><b>Last Plot Update:</b> {time_string}</p>
        <p><a href='covid19-{other_type_title.lower()}.html'>Click here to see {other_type_title} plots instead</a></p>
        <p>* <b>More Info:</b> available on <a href="https://github.com/bhbmaster/covid19">GitHub</a> and <a href="http://www.infotinks.com/coronavirus-dashboard-covid19-py/">infotinks.com</a></p>
        <p>* <b>Delta</b> is change from previous day ( + is growth; - is reduction )</p>
        <p>* <b>Ratio</b> is % change from previous day ( 1 or higher is growth; 0 to 1 is reduction )</p>
        <p>* <b>Note:</b> Peak active case prediction date is calculated using a linear regression fit on "active cases ratio" and examing its past X days values to see when it crosses 1.0.</p>
        <p>* An r<sup>2</sup> closer to 1.0 means a better prediction.</p>
        <p>* Ignore predictions with past dates.</p>
        <p>* <b>Note:</b> The plotly graphs are interactive. To have better you can click on the "Normal" or "Log" link for each country to see it's own interactive plot.</p>
        <p>There you can control control which information is plotted by clicking & double clicking on the items in the legend to isolate or disable that data.</p>
        <p>* <b>Note:</b> Data Source: <a href="https://pomber.github.io/covid19/">Pomber</a>, which generates daily json from <a href="https://github.com/CSSEGISandData/COVID-19">CSSEGISandData</a> data.</p>\n"""
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
        html += f"        <h3>#{place_num}. {country.country}</h3>\n"
        html += f"<p><a href='html-plots/{country.countryposix}-plot-NORMAL.html'>Normal</a> | <a href='html-plots/{country.countryposix}-plot-LOG.html'>Log</a></p>"
        html += f"""
        <table border="1" cellpadding="5">
        <tbody>
        <tr>
        <td>Date: {country.last_date}</td>
        <td>Last Value</td>
        <td>Last Delta Change</td>
        <td>Last Ratio Change</td>
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
        html += f"""<p>* Last percent <b>recovered</b> from all cases: {lp_recovered}%</p>
        <p>* Last percent <b>dead</b> from all cases: {lp_deaths}%</p>\n"""
        # below - ratio prediction
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
        # above prediction
        html += "        " + div+"\n"
        html += '<p>* <b>Note:</b> Data Source: <a href="https://pomber.github.io/covid19/">Pomber</a>, which generates daily json from <a href="https://github.com/CSSEGISandData/COVID-19">CSSEGISandData</a> data.</p>\n'
 
    html += f"""<!-- hitwebcounter Code START -->
<a href="https://www.hitwebcounter.com" target="_blank">
<img src="{countersite}" title="Views:" Alt="hitwebcounter" border="0" >
</a>
</body>
    </html>\n"""
    # end of html
    # make it pretty
    prettyhtml = bs4.BeautifulSoup(html, "lxml").prettify()
    # make it htmlmin
    minihtml = htmlmin.minify(prettyhtml, remove_empty_space=True)
    # write file
    with open(output_file, 'w') as file:
        file.write(minihtml)

# <!-- hitwebcounter Code START -->
# <a href="https://www.hitwebcounter.com" target="_blank">
# <img src="https://hitwebcounter.com/counter/counter.php?page=7650826&style=0024&nbdigits=9&type=page&initCount=1020" title="Free Stats for webpages" Alt="hitwebcounter"   border="0" >
# </a>                                    

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

	print("Covid19plot.py")
	print("--------------")
	

    # get and parse data
    print(f"- Downloading json from {SITE}. (please wait)")
    with urllib.request.urlopen(SITE) as url:
        data=json.loads(url.read().decode())
    if not data:
    	print(f"- Download Failed (no data).")
    print(f"- Download Complete")

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
    print(f"* # of countries {len(list_of_countries)}")

    # get world total country

    # world total not provided so we sum everything

    # get list of dates from China as it has the most most likely
    all_dates=[]
    for i in list_of_countries:
        if i.country == "China":
            all_dates=i.date_list # at this point all_dates is all of our dates
            break

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

    # create html from div list - log
    divs2html(div_list_log,"Log",start_time_string,"covid19-log.html",bootstrapped)

    # create html from div list - normal
    divs2html(div_list_normal,"Normal",start_time_string,"covid19-normal.html",bootstrapped)

    # save 
    # save_pickle(list_of_countries,"country-class-list",start_time_posix)

    # complete message
    print("Generating plots done!")

if __name__ == "__main__":
    main()

### the end ###