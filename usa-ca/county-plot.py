import pandas as pd
import plotly.graph_objects as go
import plotly.offline.offline
from plotly.subplots import make_subplots
from os import path
import plotly.express as px # for themes/templates
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

# POSSIBLE-TODO: consider removing county-pop.csv depedence as that is downloaded from new covid cases csv. its optional as population doesn't change much and it still works

### INIT ###

VersionFile = "../VERSION"  # Last Update YY.MM.DD
ndays=7 # how many days is the moving average averaging
output_html="county-output.html" # relative per population per 100K - THIS IS ORIGINAL PLOT
output_html_1="county-output-raw.html" # just raw results (Added later so its output_html_1) - THIS IS NEW PLOT
PER=100000 # we should per 100000 aka 100K
PER_TEXT="100K"
SHOW_TOP_NUMBER=12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
ThemeFile = "../PLOTLY_THEME" # contents are comma sep: theme,font family,font size
predictdays=30
COLOR_LIST = px.colors.qualitative.Vivid # this sets the colorway option in layout
COLOR_LIST_LEN = len(COLOR_LIST) # we will use the mod of this later
updatedate_dt = datetime.datetime.now()
updatedate_str = updatedate_dt.strftime("%Y-%m-%d %H:%M:%S")
csv_file = "CA-covid19cases_test.csv"
csv_file_parsable = "CA-covid19cases_test-parsable.csv"

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

# population file - NOTE: Now technically we don't need this as the information is in the CSV file
file_pop="county-pop.csv" # values from around 2020 good enough

# data input
# url_data="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv" # after March 12 2021 this data is deprecated with new data at new site
# old data site https://data.ca.gov/dataset/covid-19-cases points to new site https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state
url_data="https://data.chhs.ca.gov/dataset/f333528b-4d38-4814-bebb-12db1f10f535/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a/download/covid19cases_test.csv" # NEW

c=pd.read_csv(url_data)
print(f"RECEIVED DATA (saved to {csv_file}):")
print()
print(c.describe())
c.to_csv(csv_file)

cpops = pd.read_csv(file_pop,index_col="Rank")
# cpops = cpops.head(15)

# get top 10 (or SHOW_TOP_NUMBER) of counties based on population + select which ones to show enabled on legend
top10 = cpops.head(SHOW_TOP_NUMBER)["County"]
visible_counties = top10.values.tolist() # essentially its ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda', 'Sacramento', 'Contra Costa', 'Fresno', 'Kern', 'San Francisco']
visible_counties = ['Los Angeles', 'Santa Clara', 'San Mateo', 'San Francisco', '0-California-State']
print()
print(f"visible_counties={visible_counties}")
print()

# list of tuples [(county,pop) (county,pop)]
cpops_county_list=cpops["County"].values.tolist()
cpops_pop_list=cpops["Population"].values.tolist()
cpop_zip=zip(cpops_county_list,cpops_pop_list)
cpop_list=list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet

# print(c.head())
# print(cpops.head())

# START - convert new format to old format - START
# code converting new style csv to old style, so functions understand it
cols_to_select=["date","area","cases","cumulative_cases","deaths","cumulative_deaths"]
clean_c = c[c["date"]!="NaN"][c["area_type"]=="County"].dropna(subset=cols_to_select) # remove cols we care about that have NaN (its mostly happens in dates) & we only need Counties not State (although maybe in future can have all of california?)
prefinal_c = clean_c[cols_to_select] # now make data frame that only has cols we need
rename_dict={
    "date": "date",
    "area": "county",
    "cases": "newcountconfirmed",
    "cumulative_cases":"totalcountconfirmed",
    "deaths":"newcountdeaths",
    "cumulative_deaths":"totalcountdeaths"
}
final_c = prefinal_c.rename(columns=rename_dict) # now rename the cols to what we had in previous deprecated format
# adding california in - start
# GET CALIFORNIA STATE
cali0 = c[c["date"]!="NaN"][c["area_type"]=="State"].dropna(subset=cols_to_select)
cali1 = cali0[cols_to_select]
cali2 = cali1.rename(columns=rename_dict)
cali3 = cali2.replace("California","0-California-State")
final_c_and_cali = final_c.append(cali3,ignore_index=True) # since indexes never got messed with this in these processes we can just remove ignore_index and keep its default as False but it doesn't hurt to keep
# sidenote manually added in this line to county-pop.csv - whatever its not the prettiest i don't care: # 59,0-California-State,40129160
# adding california in - finish
c = final_c_and_cali.sort_values(by=['date']) # sort by date
print(f"CONVERTED TO PARSABLE DATA (saved to {csv_file_parsable}):")
print()
print(c.describe())
c.to_csv(csv_file_parsable)
# END - convert new format to old format - END

# raise Exception("Script stopping now until TODO implemented") # easy way to stop code while editing/fixing

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
    x=c[c.county == county]["date"].values  # same x for relative and normal plot
    # print(f"DEBUG: {x=}")
    FRONTSPACE="    "
    color_text=""
    # note where you see _1 thats for normal plot example: y is for relative original plot and y_1 is for new normal plot

    #####################################################
    # -- newcountconfirmed per 100K (moving average) -- #
    #####################################################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["newcountconfirmed"].values
    y=orgy/pop*PER  # relative plot
    y_1=orgy        # normal plot
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())          # relative plot average
    avgx_1,avgy_1=avgN(ndays,x.tolist(),y_1.tolist())    # normal plot average
    LastNewC = avgy[-1]
    LastNewC_1 = avgy_1[-1]
    print(f"{FRONTSPACE}newcountconfirmed   \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{county}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"
    legendtext_1=f"<b>{county}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy_1[-1]:0.2f}</b>"
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=1,col=1)
    fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=county,visible=visible1),row=1,col=1)
    used_colors_index = color_index # saving current color used (it follows thru the index of the colorway)

    #########################
    # linear regresion line #
    #########################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"

    # we use this code bit twice, so might as well make inner function and it only makes sense in graphing so yup here it will lie as an inner function
    def plot_regression(figure,X,Y,extralabel=""):
        # for any plot
        (success,xfinal,yfinal,r_sq,m,b0) = lastXdayslinearpredict(X,Y,predictdays) # predict days is from global
        # print(f"DEBUG PR ({extralabel}): {success=},{xfinal=},{yfinal=},{r_sq=},{m=},{b0=}")
        # if success:
        entered_prediction_if_loop = False # was used when dates were backwards and m was 0 so we didnt get prediction lines but got the other lines, however, i realized that even after we sorted the dates and it all worked out... what if we get a flat slope m=0 then issue could still happen, so i put this boolean in just in case
        if success and m != 0:
            entered_prediction_if_loop = True
            # y = mx + b ---> (y-b)/m = 0
            y_to_cross = 0
            x_cross1 = (y_to_cross - float(b0)) / float(m)
            x_cross1_int=int(x_cross1)
            day0=xfinal[0]
            day0dt = datetime.datetime.strptime(day0, "%Y-%m-%d")
            daycrossdt=day0dt+datetime.timedelta(days=int(x_cross1_int))
            daycross = daycrossdt.strftime("%Y-%m-%d")
            print(f"{FRONTSPACE}- predicted cross ({extralabel})   \t y = {m:0.4f}x+{b0:0.2f} \t r^2={r_sq:0.4f} \t {daycross=}{color_text}")
            # plot
            legendtext=f"<b>{county}</b> - predict 0 daily cases @ <b>{daycross}</b> by {predictdays}-day linear fit"
            if color_index == None:
                # if color_index is -1 we didn't set it and we will use the default color methods (next color in colorway)
                figure.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(dash='dash')),row=1,col=1)
            else:
                color_index_to_use = used_colors_index % COLOR_LIST_LEN # we circulate thru the color_way so we use modulus
                color_to_use = COLOR_LIST[color_index_to_use] # call that color via index from colorway list
                figure.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use,dash='dash')),row=1,col=1)
        return entered_prediction_if_loop, color_to_use  # return if we successfully predicted (meaning slope isnt 0 and the prediction function returned some good stuff)

    # for relative plot
    entered_prediction_if_loop, color_to_use = plot_regression(fig,avgx,avgy,"relative")
    # for normal plot
    entered_prediction_if_loop_1, color_to_use_1 = plot_regression(fig_1,avgx_1,avgy_1,"normal")
    # - sidenote the result of the relative output should equal same for normal
    # entered_prediction_if_loop, color_to_use should equal entered_prediction_if_loop_1, color_to_use_1

    ##################################################
    # -- newcountdeaths per 100K (moving average) -- #
    ##################################################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["newcountdeaths"].values
    y=orgy/pop*PER
    y_1=orgy
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    avgx_1,avgy_1=avgN(ndays,x.tolist(),y_1.tolist())
    LastNewD = avgy[-1]
    LastNewD_1 = avgy_1[-1]
    print(f"{FRONTSPACE}newcountdeaths      \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{county}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    legendtext_1=f"<b>{county}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    if color_index == None:
        fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=2,col=1)
        fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=county,visible=visible1),row=2,col=1)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use)),row=2,col=1)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use_1)),row=2,col=1)

    ##############################
    # -- total cases per 100K -- #
    ##############################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["totalcountconfirmed"].values
    y=orgy/pop*PER
    y_1=orgy
    LastC = y[-1]
    LastC_1 = y_1[-1]
    print(f"{FRONTSPACE}totalcountconfirmed \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{county}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    legendtext_1=f"<b>{county}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1),row=1,col=2)
        fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=False,legendgroup=county,visible=visible1),row=1,col=2)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use)),row=1,col=2)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=False,legendgroup=county,visible=visible1,line=dict(color=color_to_use_1)),row=1,col=2)

    ###############################
    # -- total deaths per 100K -- #
    ###############################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c.county == county]["totalcountdeaths"].values
    y=orgy/pop*PER
    y_1=orgy
    LastD = y[-1]
    LastD_1 = y_1[-1]
    print(f"{FRONTSPACE}totalcountdeaths    \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    # legendtext=f"<b>{county}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    # legendtext_1=f"<b>{county}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    # showing legend at the end as we have all of the Last data
    legendtext = f"<b>{county}</b> ({int(pop/1000):,}K) <b>{LastNewC:0.2f}</b>|{LastC:0.0f}|<b>{LastNewD:0.2f}</b>|{LastD:0.0f}"                 # trying to show every last value
    legendtext_1 = f"<b>{county}</b> ({int(pop/1000):,}K) <b>{LastNewC_1:0.2f}</b>|{int(LastC_1/1000):,}K|<b>{LastNewD_1:0.2f}</b>|{int(LastD_1):,}"       # trying to show every last value
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=True,legendgroup=county,visible=visible1),row=2,col=2)
        fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=True,legendgroup=county,visible=visible1),row=2,col=2)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=True,legendgroup=county,visible=visible1,line=dict(color=color_to_use)),row=2,col=2)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=True,legendgroup=county,visible=visible1,line=dict(color=color_to_use_1)),row=2,col=2)

### MAIN ###

# * plotly init
print()
print(f"- plotting start (theme,font,size: {Theme_Template},{Theme_Font},{Theme_FontSize})")
print()
subplot_titles = (f"Daily New Cases per {PER_TEXT} {ndays}-day Moving Average",
                  f"Total Cases per {PER_TEXT}",
                  f"Daily New Deaths per {PER_TEXT} {ndays}-day Moving Average",
                  f"Total Deaths per {PER_TEXT}")
subplot_titles_1 = (f"Daily New Cases {ndays}-day Moving Average",
                  f"Total Cases",
                  f"Daily New Deaths {ndays}-day Moving Average",
                  f"Total Deaths")
# spacings for subplots
bigportion = 0.618 # ratio of screen space for left plots
smallportion = 1-bigportion
spacing=0.05
# subplots
fig = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all
fig_1 = make_subplots(rows=2, cols=2, shared_xaxes=True, subplot_titles=subplot_titles_1, column_widths=[bigportion, smallportion],horizontal_spacing=spacing,vertical_spacing=spacing) # shared_xaxes to maintain zoom on all
random_county = cpops_county_list[0] # we picked top one which is LA (most populous at the top)
last_x = c[c.county == random_county]["date"].values.tolist()[-1]
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
    "legend_title_text": "<b>Area</b> (Pop) <b>NewC</b>|TotalC|<b>NewD</b>|TotalD"
}

fig.update_layout(title=f"<b>California Counties Covid19 Stats (Relative to Population Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str}",**plot_options) # main title & theme & hover options & font options unpacked
fig_1.update_layout(title=f"<b>California Counties Covid19 Stats (Normal / Raw Values)</b> (v{Version})<br><b>Last Data Point:</b> {last_x} , <b>Updated On:</b> {updatedate_str}",**plot_options) # main title & theme & hover options & font options unpacked
# fig = go.Figure() # then graph like this: fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=True,visible=visible1))

# * consider each county and trace it on plotly
color_index = -1 # color index, if we set to None then we alternate colors for every trace. if we set to -1 here then we match color of prediction
for county,pop in cpop_list:
    graph()
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
# print("DEBUG: colorway=",plot_options["colorway"])

### END
