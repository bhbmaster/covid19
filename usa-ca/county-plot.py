import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline.offline

### INIT ###

ndays=7 # how many days is the moving average averaging
output_html="county-output.html"

url_data="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv"
file_pop="county-pop.csv" # values from around 2020 good enough

c=pd.read_csv(url_data)

cpops = pd.read_csv(file_pop,index_col="Rank")
# cpops = cpops.head(15)

### FUNCTIONS ###

# moving average
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

# graph
def graph():
    x=c[c.county == county]["date"].values
    y=c[c.county == county]["newcountconfirmed"].values / pop * 100_000
    avgx,avgy=avgN(ndays,x.tolist(),y.tolist())
    print(f"{county} pop={pop} lastvalue{ndays}dayavg={avgy[-1]:0.2f}")
    fig.update_layout(title=f"California Counties Daily New Cases ({ndays} day Moving Average)")
    fig.add_trace(go.Scatter(x=avgx, y=avgy, name=county, showlegend=True),row=1,col=1)

### MAIN ###

# plotly init
fig = make_subplots(rows=1, cols=1)

# consider each county and trace it on plotly
for county,pop in zip(cpops["County"].values.tolist(),cpops["Population"].values.tolist()):
    graph()

# plotly
fig.write_html(output_html,auto_open=False)
div = plotly.offline.offline.plot(fig, show_link=False, include_plotlyjs=False, output_type='div')
print(div)