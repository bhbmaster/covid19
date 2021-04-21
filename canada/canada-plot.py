#### init #####

# dataset site: https://github.com/ccodwg/Covid19Canada
# link: https://github.com/ccodwg/Covid19Canada/blob/master/timeseries_prov/active_timeseries_prov.csv

# --- get data and manipulate it into correct form --- #

covid_url='https://github.com/ccodwg/Covid19Canada/blob/master/timeseries_prov/active_timeseries_prov.csv' # github
population_file='canada-pop.csv' # local - got data from wikipedia https://en.wikipedia.org/wiki/Population_of_Canada_by_province_and_territory

# --- output names --- #
covid_rx='canada.csv'
covid_final='canada-parsable.csv'
covid_html_normal='canada-output.html' # relative plots
covid_html_raw='canada-output-raw.html'

##### downloading and manipulating dataframe #####

# download
# save original
# check
# manipulate
# save final

##### plot #####

# init plots / both figures
# init settings for both figures (settings for plots and subplots)
# parse each area/province and generate trace in figure
# save html
# the end
