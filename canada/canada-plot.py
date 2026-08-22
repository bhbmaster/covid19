import pandas as pd
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import (  # local module but up one directory hence the sys path append ..
    covid_init_and_plot,
    pd_quick_info_maybe_save,
    pandas_display_options,
    read_csv_from_url,  # kept so the commented live-download remnant below still works if uncommented
    read_csv_local,
    CANADA_CASES_CSV,
    CANADA_DEATHS_CSV,
    CANADA_CASES_LOCAL_CSV,
    CANADA_DEATHS_LOCAL_CSV,
    CANADA_OPENCOVID,
)

###########################################################

### presetting pandas for correct stdout output ###

pandas_display_options()
# pd.set_option("display.max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

#### init #####

print("------------ preparing dataset -----------")
print()

# --- get data and manipulate it into correct form --- #
# Full historical provincial/territorial series from COVID-19 Canada Open Data Working Group / CovidTimelineCanada
# https://opencovid.ca/  — cases and deaths, 2020 through 2023-12-31
# Used to download live:
# covid_url_cases = CANADA_CASES_CSV
# covid_url_deaths = CANADA_DEATHS_CSV
covid_local_cases = CANADA_CASES_LOCAL_CSV
covid_local_deaths = CANADA_DEATHS_LOCAL_CSV
population_file='canada-pop.csv' # local - got data from wikipedia https://en.wikipedia.org/wiki/Population_of_Canada_by_province_and_territory

# --- output names --- #
covid_csv_rx_cases='canada-cases.csv'
covid_csv_rx_deaths='canada-deaths.csv'
covid_csv_merged='canada-merged.csv'
covid_csv_final='canada-parsable.csv'
filename_prefix="canada"
plot_title="Canada Provinces & Territories"

# --- other variables --- #

SHOW_TOP_NUMBER = 6 # 12 # how many counties to have enabled when graph shows (others can be toggled on interactively)

REGION_NAME = {
    "AB": "Alberta",
    "BC": "BC",
    "MB": "Manitoba",
    "NL": "NL",
    "NS": "Nova Scotia",
    "NT": "NWT",
    "NB": "New Brunswick",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "PEI",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}

##### downloading/accessing and manipulating population dataframe #####

cpops = pd.read_csv(population_file,index_col="Rank", skiprows=[1])  # we add skiprows=[1] to skip row 1 which is the Canada one (sidenote row 0 is column names)
cpops_prov_list = cpops["Province or Territory"].values.tolist()
cpops_pop_list = cpops["Population Est 2021"].values.tolist()
cpop_zip = zip(cpops_prov_list,cpops_pop_list)
cpop_list = list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet - now we have cpop_list=[('Alabama', 4903185), ('Alaska', 731545), ... ]

# get top 10 (or top SHOW_TOP_NUMBER)
top10 = cpops.head(SHOW_TOP_NUMBER)["Province or Territory"]
visible_provinces = top10.values.tolist()

print(f"PARSING population:")
print(f"* {cpop_list=}")
print(f"* {visible_provinces=}")
print()

##### downloading/accessing and manipulating covid dataframe #####

# Used to download live:
# print(f"* downloading Canada historical data from {CANADA_OPENCOVID}")
# print("* downloading data 1/2")
# c_cases = read_csv_from_url(covid_url_cases)
# print("* downloading data 2/2")
# c_deaths = read_csv_from_url(covid_url_deaths)
# print("* downloading data complete")
print(f"* reading Canada historical data from local files")
print(f"* original online source was {CANADA_OPENCOVID} ({CANADA_CASES_CSV} and {CANADA_DEATHS_CSV})")
print("* reading data 1/2")
c_cases = read_csv_local(covid_local_cases)
print("* reading data 2/2")
c_deaths = read_csv_local(covid_local_deaths)
print("* reading local data complete")
print()

# analyze covid cases data
pd_quick_info_maybe_save(c_cases,"RECEIVED CASES DATA",covid_csv_rx_cases)

# analyze covid deaths data
pd_quick_info_maybe_save(c_deaths,"RECEIVED DEATHS DATA",covid_csv_rx_deaths)

# Keep every historical date from either file (outer merge). Inner merge dropped
# dates that exist in only cases or only deaths, which truncated some provinces.
cases = c_cases.rename(columns={"value": "cases", "value_daily": "new_cases"})[["region", "date", "cases", "new_cases"]].copy()
deaths = c_deaths.rename(columns={"value": "deaths", "value_daily": "new_deaths"})[["region", "date", "deaths", "new_deaths"]].copy()
cases["date"] = pd.to_datetime(cases["date"], errors="coerce")
deaths["date"] = pd.to_datetime(deaths["date"], errors="coerce")
cases = cases.dropna(subset=["date", "region"])
deaths = deaths.dropna(subset=["date", "region"])

c_merged = pd.merge(cases, deaths, on=["region", "date"], how="outer")
c_merged = c_merged.sort_values(["region", "date"])
for col in ["cases", "deaths"]:
    c_merged[col] = pd.to_numeric(c_merged[col], errors="coerce")
    c_merged[col] = c_merged.groupby("region")[col].ffill().fillna(0)
for col in ["new_cases", "new_deaths"]:
    c_merged[col] = pd.to_numeric(c_merged[col], errors="coerce").fillna(0)
c_merged["date"] = c_merged["date"].dt.strftime("%Y-%m-%d")
c_merged["area"] = c_merged["region"].replace(REGION_NAME)
c_merged_final = c_merged[["date", "area", "cases", "new_cases", "deaths", "new_deaths"]]
pd_quick_info_maybe_save(c_merged_final, "MERGED_FINAL", covid_csv_merged)
c0 = c_merged_final

# find all unique provinces and compare with population (they must match)
unique_provinces = sorted(c0["area"].unique().tolist())
print(f"* covid data -> {unique_provinces=} , length {len(unique_provinces)}")
cpops_prov_list_sorted = sorted(cpops_prov_list)
print(f"* population -> {cpops_prov_list_sorted=} , length {len(cpops_prov_list_sorted)}")
print(f"* Do we get the same areas from Covid Data and Population data: {cpops_prov_list_sorted==unique_provinces}")
print(f"* date range: {c0['date'].min()} through {c0['date'].max()}")

# sort by date
c2 = c0.sort_values(by=["date", "area"])

# show results of final data frame before plotting
print()
pd_quick_info_maybe_save(c2, "FINAL DATA", covid_csv_final)

#################################################
#                     PLOT                      #
#################################################

# plot
covid_init_and_plot(c2,cpop_list,filename_prefix,plot_title,[ "date", "area", "cases", "deaths", "new_cases", "new_deaths" ],visible_provinces,to_get_to_root="..",DEBUGAREA="")

##### END #####
