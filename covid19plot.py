import json
import urllib.request
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline.offline
# import plotly.plotly as py
import string
import os
import datetime

# By: Kostia Khlebopros #
# Last Update: 2020-04-09 #

# constants

SITE="https://pomber.github.io/covid19/timeseries.json"
start_time = datetime.datetime.now()
start_time_string = start_time.strftime("%Y-%m-%d %H:%M:%S")

### classes ###

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

### main ###

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

# get world total
# get list of dates from China as it has the most most likely
all_dates=[]
for i in list_of_countries:
    if i.country == "China":
        all_dates=i.date_list # at this point all_dates is all of our dates
        break

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

# def mykey(x):
#    return x.last_cases
# list_of_countries.sort(key=mykey, reverse=True)

list_of_countries.sort(key=lambda x: x.last_cases, reverse=True)

# plot all
rows=len(list_of_countries)
n=1
valid_chars="-_.%s%s" % (string.ascii_letters, string.digits)
div_list_log=[]
div_list_normal=[]
# if not os.path.exists("html-plots"):
#    os.mkdir("html-plots")
# if not os.path.exists("img-plots"):
#    os.mkdir("img-plots")
for i in list_of_countries:
    country_name=i.country
    file_country_name=''.join(c for c in country_name if c in valid_chars)
    ### log ###
    full_path_html=f"html-plots/{file_country_name}-plot-LOG.html"
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
    fig.update_yaxes(type="log",row=1,col=1)
    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=1)
    # fig.write_html(full_path_html,auto_open=False) # write 2.5 MiB html file
    div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
    div_list_log.append(div)
    ### normal ###
    full_path_html=f"html-plots/{file_country_name}-plot-NORMAL.html"
    fig = make_subplots(rows=2, cols=1)
    fig.update_layout(title=f"COVID19 - {country_name}")    
    fig.add_trace(go.Scatter(x=i.date_list, y=i.cases_list, name="Cases", line=dict(color='firebrick', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.deaths_list, name="Deaths", line=dict(color='red', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.recovered_list, name="Recovered", line=dict(color='green', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.active_list, name="Active Cases (Cases - Deaths & Recovered)", line=dict(color='purple', width=2),showlegend=True),row=1,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_cases_list, name="Ratio Diff Cases", showlegend=True),row=2,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_active_list, name="Ratio Diff Active Cases", showlegend=True),row=2,col=1)
    # fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_recovered_list, name="Ratio Diff Recovered", showlegend=True),row=2,col=1)
    fig.add_trace(go.Scatter(x=i.date_list, y=i.delta_ratio_deaths_list, name="Ratio Diff Deaths", showlegend=True),row=2,col=1)
    fig.update_yaxes(type=None,row=1,col=1)
    fig.update_yaxes(type=None,rangemode="tozero",row=2,col=1)
    # fig.write_html(full_path_html,auto_open=False) # write 2.5 MiB html file
    div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
    div_list_normal.append(div)
    ### done plot ###
    print(f"{n}/{rows} - {country_name} - last value from {i.last_date} with {i.last_cases} cases, {i.last_deaths} deaths, {i.last_recovered} recovered, {i.last_active} active cases.")
    n+=1

### create html - log ###

html="""<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>"""
html+=f"<p><b>covid19.py stats (LOG) - Last Update: {start_time_string}</b></p>"
for i in div_list_log:
    # html+="<p>-------------------------</p>"
    html+=i

with open('covid19-log.html', 'w') as file:
    file.write(html)

### create html - normal ###

html="""<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>"""
html+=f"<p><b>covid19.py stats (NORMAL) - Last Update: {start_time_string}</b></p>"
for i in div_list_normal:
    # html+="<p>-------------------------</p>"
    html+=i

with open('covid19-normal.html', 'w') as file:
    file.write(html)

### almost done

print("Generating plots done!")

### the end ###