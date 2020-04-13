import json
import urllib.request
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline.offline
# import plotly.plotly as py
import string
# import os
import datetime
import bs4
import htmlmin
import numpy as np
from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures

# By: Kostia Khlebopros
# Site: http://www.infotinks.com/coronavirus-dashboard-covid19-py/
# Github: https://github.com/bhbmaster/covid19
# Last Update: 2020-04-11

### constants ###

SITE="https://pomber.github.io/covid19/timeseries.json"
start_time = datetime.datetime.now()
start_time_string = start_time.strftime("%Y-%m-%d %H:%M:%S")
valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
bootstrapped = False
predictdays=5

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
        self.length=len(entrylist)
        self.last_date=entrylist[self.length-1].date
        self.last_cases=entrylist[self.length-1].cases
        self.last_deaths=entrylist[self.length-1].deaths
        self.last_recovered=entrylist[self.length-1].recovered
        self.last_active=entrylist[self.length-1].active
        self.last_delta_cases = entrylist[self.length - 1].delta_cases
        self.last_delta_active = entrylist[self.length - 1].delta_active
        self.last_delta_recovered = entrylist[self.length - 1].delta_recovered
        self.last_delta_deaths = entrylist[self.length - 1].delta_deaths
        self.last_delta_ratio_cases = entrylist[self.length - 1].delta_ratio_cases
        self.last_delta_ratio_active = entrylist[self.length - 1].delta_ratio_active
        self.last_delta_ratio_recovered = entrylist[self.length - 1].delta_ratio_recovered
        self.last_delta_ratio_deaths = entrylist[self.length - 1].delta_ratio_deaths
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
    file_country_name=''.join(c for c in country_name if c in valid_chars)
    full_path_html=f"html-plots/{file_country_name}-plot-{the_type_string}.html"
    fig = make_subplots(rows=2, cols=1)
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
    # success, xfinal, yfinal, r_sq, m, b0 = i.lastXdayslinearpredict(i.delta_ratio_active_list, 10)
    # if success:
    #     fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name="Predicted Ratio Active Cases", line=dict(color='gray', width=1), showlegend=True), row=2,col=1)
    # above  - ratio prediction
    fig.update_yaxes(type=the_type_fig,row=1,col=1)
    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=1)
    # fig.write_html(full_path_html,auto_open=False) # write 2.5 MiB html file
    div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
    return div

# create html file out of div list

def divs2html(div_list,type_title,time_string,output_file,bootstrap_on=False):
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
	    </style>
    <head/>
    <body>
        <h2>Covid19.py Plots ({type_title})</h2>
        <p><b>Last Update:</b> {time_string}</p>
        <p><b>* More Info:</b> available on <a href="https://github.com/bhbmaster/covid19">GitHub</a> and <a href="http://www.infotinks.com/coronavirus-dashboard-covid19-py/">infotinks.com</a></p>
        <p><b>* Delta</b> is change from previous day ( + is growth; - is reduction )</p>
        <p><b>* Ratio</b> is % change from previous day ( 1 or higher is growth; 0 to 1 is reduction )</p>
        <p>* <b>Note:</b> Maximum active case prediction date is calculated using past 10 days of active cases ratio and a linear regression fit to see when it crosses 1.0.</p>\n"""
    # print("HTML START:")
    # print(html)
    # print("HTML END:")
    for country,div in div_list:
        html += f"        <h3>{country.country}</h3>\n"
        html += f"""
        <table border="1" cellpadding="5">
        <tbody>
        <tr>
        <td>Date: {country.last_date}</td>
        <td>Last Value</td>
        <td>Delta Change</td>
        <td>Ratio Change</td>
        </tr>
        <tr>
        <td>Cases</td>
        <td>{country.last_cases}</td>
        <td>{country.last_delta_cases}</td>
        <td>{country.last_delta_ratio_cases}</td>
        </tr>
        <tr>
        <td>Deaths</td>
        <td>{country.last_deaths}</td>
        <td>{country.last_delta_deaths}</td>
        <td>{country.last_delta_ratio_deaths}</td>
        </tr>
        <tr>
        <td>Recovered</td>
        <td>{country.last_recovered}</td>
        <td>{country.last_delta_recovered}</td>
        <td>{country.last_delta_ratio_recovered}</td>
        </tr>
        <tr>
        <td>Active Cases</td>
        <td>{country.last_active}</td>
        <td>{country.last_delta_active}</td>
        <td>{country.last_delta_ratio_active}</td>
        </tr>
        </tbody>
        </table>\n"""
        # below - ratio prediction
        success, xfinal, yfinal, r_sq, m, b0 = country.lastXdayslinearpredict(country.delta_ratio_active_list, predictdays)
        if success:
            try:
                x_cross1 = (1.0 - float(b0)) / float(m)
                x_cross1_int=int(x_cross1)
                day0=xfinal[0]
                day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")
                daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))
                daycross = daycrossdt.strftime("%Y-%m-%d")
                html += f"<p>* Active Cases predicted to hit peak @ {daycross}</p>\n"
            except:
                success=False
        # above prediction
        html += "        " + div+"\n"
    html += "</body>\n"
    html += "</html>"
    # end of html
    # make it pretty
    prettyhtml = bs4.BeautifulSoup(html, "lxml").prettify()
    # make it htmlmin
    minihtml = htmlmin.minify(prettyhtml, remove_empty_space=True)
    # write file
    with open(output_file, 'w') as file:
        file.write(minihtml)

### main ###

def main():

    # get and parse data

    with urllib.request.urlopen(SITE) as url:
        data=json.loads(url.read().decode())

    # last_date=data["China"][len(data["China"])-1]["date"]  # returns 2020-3-14

    last_confirmed=0
    last_deaths=0
    last_recovered=0
    last_active = 0

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
    # if not os.path.exists("html-plots"):
    #    os.mkdir("html-plots")
    # if not os.path.exists("img-plots"):
    #    os.mkdir("img-plots")

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

    # complete message
    print("Generating plots done!")

if __name__ == "__main__":
    main()

### the end ###