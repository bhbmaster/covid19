import string
import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures
from scipy.optimize import curve_fit
import plotly.graph_objects as go
import plotly.express as px # for themes/templates

# used by covid19plot.py and usa-ca/country-plot.py

### globals ###

valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
PER = 100000 # when we display relative data this is the per value so we do per 100,000 people aka 100K
PER_TEXT = "100K" # text version, so we type less when we talk about it
ndays = 7 # how many days is the moving average averaging
predictdays = 30 # how many days to predict back and forward with linear regression fit
COLOR_LIST = px.colors.qualitative.Vivid # this sets the colorway option in layout
COLOR_LIST_LEN = len(COLOR_LIST) # we will use the mod of this later

### functions ###

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

# input x dates and y values lists, output x (date list) and y (values) and r^2 and m and b0. uses last X days to predict
# note already have a form of it in Country class below but we recreated it so it works without class here (POSSIBLE-TODO: might be good idea to get into common)
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

# * show human number : example 3 becomes 3, 10123 become 10.1K, 10022020 becomes 10M
def human_number(number):
    if number < 1_000: # 0 - 999
        return f"{number}"
    if number < 10_000: # 1,000 - 9,999
        return f"{number/1_000:0.2f}K"
    if number < 100_000: # 10,000 -  99,999
        return f"{number/1_000:0.1f}K"
    if number < 1_000_000: # 100,000 - 999,999
        return f"{int(number/1_000):,}K"
    if number < 10_000_000: # 1,000,000 - 9,999,999
        return f"{number/1_000_000:0.2f}M"
    if number < 100_000_000: # 10,000,000 - 99,999,999
        return f"{number/1_000_000:0.1f}M"
    else: # 100,000,000 and above
        return f"{int(number/1_000_000):,}M"

# * graph - used in usa states & california plots
# providing "fig" and "fig_1" to plot on. the dataframe to use as "c".
# "area" is the name of the state/county or area, "pop" is the population in that area
# the names of the columns:
# nX = name of the date column (which is our X values)
# nA = name of area column
# nC = name of cases column
# nD = name of deaths column
# nNC = name of new cases column
# nND = name of new deaths column
# "visible_area" = list of areas to show
# "color_index" = if originally set to None then we alternate colors for every trace. if originally we set to -1 here then we match color of prediction
def graph(fig, fig_1, area, pop, c, nX, nA, nC, nD, nNC, nND, visible_areas, color_index):
    # global color_index
    print(f"- {area} pop={pop} - last recorded values below:")
    visible1 = "legendonly" if not area in visible_areas else None
    x=c[c[nA] == area]["date"].values  # same x for relative and normal plot
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
    orgy=c[c[nA] == area][nNC].values
    y=orgy/pop*PER  # relative plot
    y_1=orgy        # normal plot
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())          # relative plot average
    avgx_1,avgy_1=avgN(ndays,x.tolist(),y_1.tolist())    # normal plot average
    LastNewC = avgy[-1]
    LastNewC_1 = avgy_1[-1]
    print(f"{FRONTSPACE}NewCases   \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{area}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"
    legendtext_1=f"<b>{area}</b> pop={pop:,} NewC<sub>final</sub>=<b>{avgy_1[-1]:0.2f}</b>"
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=area,visible=visible1),row=1,col=1)
    fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1),row=1,col=1)
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
            # legendtext=f"<b>{area}</b> - predict 0 daily cases @ <b>{daycross}</b> by {predictdays}-day linear fit"
            legendtext=f"> PREDICT no new cases in <b>{area}</b> on <b>{daycross}</b>"
            if color_index == None:
                # if color_index is -1 we didn't set it and we will use the default color methods (next color in colorway)
                figure.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(dash='dash')),row=1,col=1)
            else:
                color_index_to_use = used_colors_index % COLOR_LIST_LEN # we circulate thru the color_way so we use modulus
                color_to_use = COLOR_LIST[color_index_to_use] # call that color via index from colorway list
                figure.add_trace(go.Scatter(x=xfinal, y=yfinal, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use,dash='dash')),row=1,col=1)
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
    orgy=c[c[nA] == area][nND].values
    y=orgy/pop*PER
    y_1=orgy
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    avgx_1,avgy_1=avgN(ndays,x.tolist(),y_1.tolist())
    LastNewD = avgy[-1]
    LastNewD_1 = avgy_1[-1]
    print(f"{FRONTSPACE}NewDeaths      \t x = {avgx[-1]} \t org_y = {orgy[-1]:0.0f} \t {ndays}day_avg_y_per{PER_TEXT} = {avgy[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{area}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    legendtext_1=f"<b>{area}</b> pop={pop:,} NewD<sub>final</sub>=<b>{avgy_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    if color_index == None:
        fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=area,visible=visible1),row=2,col=1)
        fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1),row=2,col=1)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=avgx, y=avgy, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use)),row=2,col=1)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=avgx_1, y=avgy_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use_1)),row=2,col=1)

    ##############################
    # -- total cases per 100K -- #
    ##############################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c[nA] == area][nC].values
    y=orgy/pop*PER
    y_1=orgy
    LastC = y[-1]
    LastC_1 = y_1[-1]
    print(f"{FRONTSPACE}TotalCases \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    legendtext=f"<b>{area}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    legendtext_1=f"<b>{area}</b> pop={pop:,} TotC<sub>final</sub>=<b>{y_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=area,visible=visible1),row=1,col=2)
        fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1),row=1,col=2)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use)),row=1,col=2)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=False,legendgroup=area,visible=visible1,line=dict(color=color_to_use_1)),row=1,col=2)

    ###############################
    # -- total deaths per 100K -- #
    ###############################

    if color_index != None:
        # go to next color index (if we use it save it and use modulus of length)
        color_index += 1
        color_text=f"\tcolor={color_index}"
    orgy=c[c[nA] == area][nD].values
    y=orgy/pop*PER
    y_1=orgy
    LastD = y[-1]
    LastD_1 = y_1[-1]
    print(f"{FRONTSPACE}TotalDeaths    \t x = {x[-1]} \t org_y = {orgy[-1]:0.0f} \t y_per{PER_TEXT} = {y[-1]:0.2f}{color_text}") # print statement luckily shows both relative + normal
    # legendtext=f"<b>{area}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y[-1]:0.2f}</b>"        # this is not shown - but have it just in case
    # legendtext_1=f"<b>{area}</b> pop={pop:,} TotD<sub>final</sub>=<b>{y_1[-1]:0.2f}</b>"    # this is not shown - but have it just in case
    # showing legend at the end as we have all of the Last data
    legendtext = f"<b>{area}</b> ({human_number(pop)}) <b>{LastNewC:0.2f}</b>|{human_number(LastC)}|<b>{LastNewD:0.2f}</b>|{LastD:0.0f}"                 # trying to show every last value
    legendtext_1 = f"<b>{area}</b> ({human_number(pop)}) <b>{LastNewC_1:0.2f}</b>|{human_number(LastC_1)}|<b>{LastNewD_1:0.2f}</b>|{int(LastD_1):,}"       # trying to show every last value
    if color_index == None:
        fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=True,legendgroup=area,visible=visible1),row=2,col=2)
        fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=True,legendgroup=area,visible=visible1),row=2,col=2)
    else:
        if entered_prediction_if_loop:
            fig.add_trace(go.Scatter(x=x, y=y, name=legendtext, showlegend=True,legendgroup=area,visible=visible1,line=dict(color=color_to_use)),row=2,col=2)
        if entered_prediction_if_loop_1:
            fig_1.add_trace(go.Scatter(x=x, y=y_1, name=legendtext_1, showlegend=True,legendgroup=area,visible=visible1,line=dict(color=color_to_use_1)),row=2,col=2)

    # return the altered plotly figures which now have all of the plots & also we return the color_index as we keep track of it for next plot
    return fig, fig_1, color_index

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
        except Exception as err:
            success=False
            xfinal=None
            yfinal=None
            r_sq=None
            m=None
            b0=None
            print("* WARNING in lastXdayslinearpredict:", err)
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
        except Exception as err:
            success=False
            xfinal=None
            yfinal=None
            a=None
            b=None
            c=None
            print("* WARNING in lastXdayscurvefit:", err)
        return (success,xfinal,yfinal,a,b,c)