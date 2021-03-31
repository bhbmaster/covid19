import string
import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures
from scipy.optimize import curve_fit

# used by covid19plot.py and usa-ca/country-plot.py

### globals ###

valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)

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

### classes ###

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