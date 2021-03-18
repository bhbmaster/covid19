import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots
from os import path
import plotly.express as px # for themes/templates
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

### INIT ###

VersionFile = "../VERSION"  # Last Update YY.MM.DD
ndays=7 # how many days is the moving average averaging
output_html="county-output.html"
PER=100000 # we should per 100000 aka 100K
PER_TEXT="100K"
SHOW_TOP_NUMBER=12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
ThemeFile = "../PLOTLY_THEME" # contents are comma sep: theme,font family,font size
predictdays=30
COLOR_LIST = px.colors.qualitative.Vivid # this sets the colorway option in layout
COLOR_LIST_LEN = len(COLOR_LIST) # we will use the mod of this later
updatedate_dt = datetime.datetime.now()
updatedate_str = updatedate_dt.strftime("%Y-%m-%d %H:%M:%S")


# colorway options:
# >>> dir(px.colors.qualitative)
# ['Alphabet', 'Alphabet_r', 'Antique', 'Antique_r', 'Bold', 'Bold_r', 'D3', 'D3_r', 'Dark2', 'Dark24', 'Dark24_r', 'Dark2_r', 'G10', 'G10_r', 'Light24', 'Light24_r', 'Pastel', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'Pastel_r', 'Plotly', 'Plotly_r', 'Prism', 'Prism_r', 'Safe', 'Safe_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'T10', 'T10_r', 'Vivid', 'Vivid_r', '__all__', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', '_cols', '_contents', '_k', '_swatches', 'swatches']

# Get Version
Version = open(VersionFile,"r").readline().rstrip().lstrip() if path.exists(VersionFile) else "NA"

# Get Theme
ThemeFileContents = open(ThemeFile,"r").readline().rstrip().lstrip().split(",")
Theme_Template = ThemeFileContents[0] if path.exists(ThemeFile) else "none"
Theme_Font = ThemeFileContents[1] if path.exists(ThemeFile) else "Arial"
Theme_FontSize = int(ThemeFileContents[2]) if path.exists(ThemeFile) else 12

# population file
file_pop="county-pop.csv" # values from around 2020 good enough

# data input - TODO: implement new CSV
# url_data="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv" # after March 12 2021 this data is deprecated with new data at new site
# old data site https://data.ca.gov/dataset/covid-19-cases points to new site https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state
url_data="https://data.chhs.ca.gov/dataset/f333528b-4d38-4814-bebb-12db1f10f535/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a/download/covid19cases_test.csv" # NEW
raise Exception("Script stopping now until TODO implemented")

c=pd.read_csv(url_data)
print(c.describe())

cpops = pd.read_csv(file_pop,index_col="Rank")
# cpops = cpops.head(15)

# get top 10 (or SHOW_TOP_NUMBER) of counties based on population + select which ones to show enabled on legend
top10 = cpops.head(SHOW_TOP_NUMBER)["County"]
visible_counties = top10.values.tolist() # essentially its ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda', 'Sacramento', 'Contra Costa', 'Fresno', 'Kern', 'San Francisco']
visible_counties = ['Los Angeles', 'Santa Clara', 'San Mateo', 'San Francisco']
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

# input x dates and y values lists, output x (date list) and y (values) and r^2 and m and b0. uses last X days to predict
def lastXdayslinearpredict(x_dates, y_values, days=10):
    success=True
    try:
        # grab last 10 days or whatever
        days=int(days)
        x0=x_dates[-(days+1):-1]
        y0=y_values[-(days+1):-1]
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
    except Exception as e:
        print("LINEAR FIT ERROR:",e)
        success=False
        xfinal=None
        yfinal=None
        r_sq=None
        m=None
        b0=None
    return (success,xfinal,yfinal,r_sq,m,b0)

# * graph
def graph():
    global color_index
    print(f"* {county} pop={pop} - last recorded values below:")
    visible1 = "legendonly" if not county in visible_counties else None
    x=c[c.county == county]["date"].values
    FRONTSPACE="    "
    color_text=""

    #####################################################
    # -- newcountconfirmed per 100K (moving average) -- #
    #####################################################
    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["newcountconfirmed"].values
    y=orgy/pop*PER
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    print(f"{FRONTSPACE}newcountconfirmed   \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}")
    legendtext=f"<b>{county}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=True,legendgroup=county,visible=visible1),row=1,col=1)
    used_colors_index = color_index # saving current color used (it follows thru the index of the colorway)

    #########################
    # linear regresion line #
    #########################
    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    (success,xfinal,yfinal,r_sq,m,b0) = lastXdayslinearpredict(avgx,avgy,predictdays)
    # print(f"DEBUG: {success=},{xfinal=},{yfinal=},{r_sq=},{m=},{b0=}")
    if success:
        # y = mx + b ---> (y-b)/m = 0
        y_to_cross = 0
        x_cross1 = (y_to_cross - float(b0)) / float(m) 
        x_cross1_int=int(x_cross1)
        day0=xfinal[0]
        day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")
        daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))
        daycross = daycrossdt.strftime("%Y-%m-%d")
        print(f"{FRONTSPACE}- predicted cross   \t y = {m:0.4f}x+{b0:0.2f} \t r^2={r_sq:0.4f} \t {daycross=}{color_text}")
        # plot
        legendtext=f"<b>{county}</b> - predict 0 daily cases @ <b>{daycross}</b> by {predictdays}-day linear fit"
        if color_index == None:
            # if color_index is -1 we didn't set it and we will use the default color methods (next color in colorway)
            fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext+f"", showlegend=False,legendgroup=county,visible=visible1,line=dict(dash='dash')),row=1,col=1)
        else:
            color_index_to_use = used_colors_index % COLOR_LIST_LEN # we circulate thru the color_way so we use modulus
            color_to_use = COLOR_LIST[color_index_to_use] # call that color via index from colorway list
            fig.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext+f"", showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use,dash='dash')),row=1,col=1)

    ##################################################
    # -- newcountdeaths per 100K (moving average) -- #
    ##################################################
    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["newcountdeaths"].values
    y=orgy/pop*PER
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    print(f"{FRONTSPACE}newcountdeaths      \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}")
    legendtext=f"<b>{county}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"
    if color_index == None:
        fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=2,col=1)
    else:
        fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use)),row=2,col=1)

    ##############################
    # -- total cases per 100K -- #
    ##############################
    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["totalcountconfirmed"].values
    y=orgy/pop*PER
    print(f"{FRONTSPACE}totalcountconfirmed \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}")
    legendtext=f"<b>{county}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y[-1]:0.2f}</b>"
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=1,col=2)
    else:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use)),row=1,col=2)


    ###############################
    # -- total deaths per 100K -- #
    ###############################
    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["totalcountdeaths"].values 
    y=orgy/pop*PER
    print(f"{FRONTSPACE}totalcountdeaths    \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}")
    legendtext=f"<b>{county}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y[-1]:0.2f}</b>"
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=2,col=2)
    else:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use)),row=2,col=2)

### MAIN ###

# * plotly init
print(f"- plotting start (theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize})")
subplot_titles = (f"Daily New Cases per {PER_TEXT} {ndays}-day Moving Average",
                  f"Total Cases per {PER_TEXT}",
                  f"Daily New Deaths per {PER_TEXT} {ndays}-day Moving Average",
                  f"Total Deaths per {PER_TEXT}")
# spacings for subplots
bigportion = 0.618 # ratio of screen space for left plots
smallportion = 1-bigportion
spacing=0.05
# subplots
fig = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all
random_county = cpops_county_list[0] # we picked top one which is LA (most populous at the top)
last_x = c[c.county == random_county]["date"].values.tolist()[-1]
# supported fonts: https://plotly.com/python/reference/layout/
plot_options={
    "hoverlabel_font_size": Theme_FontSize,
    "title_font_size": Theme_FontSize+2,
    "legend_font_size": Theme_FontSize-1,
    "font_size": Theme_FontSize,
    "hoverlabel_font_family": Theme_Font,
    "title_font_family": Theme_Font,
    "legend_font_family": Theme_Font,
    "font_family": Theme_Font,
    "hoverlabel_namelength": -1,  # the full line instead of the default 15
    "hovermode": 'x',
    "template": Theme_Template,
    "colorway": COLOR_LIST
}

fig.update_layout(title=f"<b>California Counties Covid19 Stats</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str}",**plot_options) # main title & theme & hover options & font options unpacked
# fig = go.Figure() # then graph like this: fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=True,visible=visible1))

# * consider each county and trace it on plotly
color_index = -1 # color index, if we set to None then we alternate colors for every trace. if we set to -1 here then we match color of prediction
for county,pop in cpop_list:
    graph()

# * plotly generate html output generation
fig.write_html(output_html,auto_open=False)

# * html div generation (not used)
div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
print(f"len(div)={len(div)}") # div not used
print("- plotting end")
# print("DEBUG: colorway=",plot_options["colorway"])

### END
