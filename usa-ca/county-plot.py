import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots

### INIT ###

ndays=7 # how many days is the moving average averaging
output_html="county-output.html"
PER=100000 # we should per 100000 aka 100K
PER_TEXT="100K"
SHOW_TOP_NUMBER=12 # how many counties to have enabled when graph shows (others can be toggled on interactively)

# data input
url_data="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv"
file_pop="county-pop.csv" # values from around 2020 good enough

c=pd.read_csv(url_data)
print(c.describe())

cpops = pd.read_csv(file_pop,index_col="Rank")
# cpops = cpops.head(15)

# top 12 most populous counties
top10 = cpops.head(SHOW_TOP_NUMBER)["County"]
visible_counties = top10.values.tolist() # essentially its ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda', 'Sacramento', 'Contra Costa', 'Fresno', 'Kern', 'San Francisco']
print(f"visible_counties={visible_counties}")

# list of tuples [(county,pop) (county,pop)]
cpops_county_list=cpops["County"].values.tolist()
cpops_pop_list=cpops["Population"].values.tolist()
cpop_zip=zip(cpops_county_list,cpops_pop_list)
cpop_list=list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet

### FUNCTIONS ###

# * moving average
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

# * graph
def graph():
    print(f"* {county} pop={pop} - last recoded values below:")
    visible1 = "legendonly" if not county in visible_counties else None
    x=c[c.county == county]["date"].values
    FRONTSPACE="    "
    # -- newcountconfirmed per 100K (moving average) -- #
    orgy=c[c.county == county]["newcountconfirmed"].values
    y=orgy/pop*PER
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    print(f"{FRONTSPACE}newcountconfirmed   \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}")
    legendtext=f"<b>{county}</b> (pop {pop:,}) is <b>{avgy[-1]:0.2f}</b> on {avgx[-1]}"
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=True,legendgroup=county,visible=visible1),row=1,col=1)
    # -- newcountdeaths per 100K (moving average) -- #
    orgy=c[c.county == county]["newcountdeaths"].values
    y=orgy/pop*PER
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    print(f"{FRONTSPACE}newcountdeaths      \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}")
    legendtext=f"<b>{county}</b> (pop {pop:,}) is <b>{avgy[-1]:0.2f}</b> on {avgx[-1]}"
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=2,col=1)
    # -- total cases per 100K -- #
    orgy=c[c.county == county]["totalcountconfirmed"].values
    y=orgy/pop*PER
    print(f"{FRONTSPACE}totalcountconfirmed \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}")
    legendtext=f"<b>{county}</b> (pop {pop:,}) is <b>{y[-1]:0.2f}</b> on {x[-1]}"
    fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=3,col=1)
    # -- total deaths per 100K -- #
    orgy=c[c.county == county]["totalcountdeaths"].values 
    y=orgy/pop*PER
    print(f"{FRONTSPACE}totalcountdeaths    \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}")
    legendtext=f"<b>{county}</b> (pop {pop:,}) is <b>{y[-1]:0.2f}</b> on {x[-1]}"
    fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=4,col=1)


### MAIN ###

# * plotly init
print("- plotting start")
subplot_titles = (f"Daily New Cases per {PER_TEXT} {ndays}-day Moving Average",
                  f"Daily New Deaths per {PER_TEXT} {ndays}-day Moving Average",
                  f"Total Cases per {PER_TEXT}",
                  f"Total Deaths per {PER_TEXT}")
fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=subplot_titles) # shared_xaxes to maintain zoom on all
random_county = cpops_county_list[0] # we picked top one which is LA (most populous at the top)
last_x = c[c.county == random_county]["date"].values.tolist()[-1]
fig.update_layout(title=f"California Counties Covid Stats (Last Update: {last_x})")
# fig = go.Figure() # then graph like this: fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=True,visible=visible1))

# * consider each county and trace it on plotly
for county,pop in cpop_list:
    graph()

# * plotly generate html output generation
fig.write_html(output_html,auto_open=False)

# * html div generation (not used)
div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
print(f"len(div)={len(div)}") # div not used
print("- plotting end")

### END
