import pandas as pd
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import covid_init_and_plot, pd_quick_info_maybe_save  # local module but up one directory hence the sys path append ..

###########################################################

### presetting pandas for correct stdout output ###

pd.set_option("max_colwidth", None)
# pd.set_option("max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

#### init #####

print("------------ preparing dataset -----------")
print()

# --- get data and manipulate it into correct form --- #
# new data source started using on 2022-08-13 provided by "COVID-19 Canada Open Data Working Group" on https://opencovid.ca/
covid_url_cases='https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/cases_pt.csv'
covid_url_deaths='https://raw.githubusercontent.com/ccodwg/CovidTimelineCanada/main/data/pt/deaths_pt.csv'
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

print("* downloading data 1/2")
c_cases = pd.read_csv(covid_url_cases) ####### new for fixing canada-plot
print("* downloading data 2/2")
c_deaths = pd.read_csv(covid_url_deaths) ####### new for fixing canada-plot
print("* downloading data complete")
print()

# analyze covid cases data ####### new for fixing canada-plot
pd_quick_info_maybe_save(c_cases,"RECEIVED CASES DATA",covid_csv_rx_cases)
c_cases_original = c_cases

# analyze covid deaths data ####### new for fixing canada-plot
pd_quick_info_maybe_save(c_deaths,"RECEIVED DEATHS DATA",covid_csv_rx_deaths)
c_deaths_original = c_deaths

# how merge tables https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html#brief-primer-on-merge-methods-relational-algebra
# reference target column names
# ,date,area,cases,new_cases,deaths,new_deaths

# (MERGE1) merge with cases on the left, deaths on the right
c_merged = pd.merge(c_cases, c_deaths, on=["region", "date"])
del c_merged["name_x"]
del c_merged["name_y"]
rename_dict = {"region": "area", "value_x":"cases", "value_daily_x":"new_cases", "value_y":"deaths", "value_daily_y":"new_deaths" }
c_merged_mod_renamed = c_merged.rename(columns=rename_dict)

# (MERGE2) merge with deaths on the left, cases on the right
c_merged_OTHER = pd.merge(c_deaths, c_cases, on=["region", "date"])
del c_merged_OTHER["name_x"]
del c_merged_OTHER["name_y"]
rename_dict_OTHER = {"region": "area", "value_y":"cases", "value_daily_y":"new_cases", "value_x":"deaths", "value_daily_x":"new_deaths" }
c_merged_mod_renamed_OTHER = c_merged_OTHER.rename(columns=rename_dict_OTHER)

# pick the merge which has more items (MERGE1 cases on the right, or MERGE2 deaths on the right). if the same pick item 1
row_count_cd = c_merged_mod_renamed.shape[0]
row_count_dc = c_merged_mod_renamed_OTHER.shape[0]
c_merged_final = c_merged_mod_renamed if row_count_cd >= row_count_dc else c_merged_mod_renamed_OTHER
pd_quick_info_maybe_save(c_merged_final, "MERGED_FINAL", covid_csv_merged)
c0 = c_merged_final

# Rename the provinces in the given dataframe to match the population dataframes provinces (for the relative to population stats)
# GIVEN:  * covid data -> unique_provinces=['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'] , length 13
# TARGET: * population -> cpops_prov_list_sorted=['Alberta', 'BC', 'Manitoba', 'NL', 'NWT', 'New Brunswick', 'Nova Scotia', 'Nunavut', 'Ontario', 'PEI', 'Quebec', 'Saskatchewan', 'Yukon'] , length 13
# * Do we get the same areas from Covid Data and Population data: False
c0["area"] = c0["area"].replace("AB","Alberta")
c0["area"] = c0["area"].replace("BC","BC")
c0["area"] = c0["area"].replace("MB","Manitoba")
c0["area"] = c0["area"].replace("NL","NL")
c0["area"] = c0["area"].replace("NS","Nova Scotia")
c0["area"] = c0["area"].replace("NT","NWT")
c0["area"] = c0["area"].replace("NB","New Brunswick")
c0["area"] = c0["area"].replace("NU","Nunavut")
c0["area"] = c0["area"].replace("ON","Ontario")
c0["area"] = c0["area"].replace("PE","PEI")
c0["area"] = c0["area"].replace("QC","Quebec")
c0["area"] = c0["area"].replace("SK","Saskatchewan")
c0["area"] = c0["area"].replace("YT","Yukon")
c1 = c0

# find all unique provinces and compare with population (they must match)
unique_provinces = list(set(c1["area"].values.tolist()))
unique_provinces.sort()
print(f"* covid data -> {unique_provinces=} , length {len(unique_provinces)}")
cpops_prov_list_sorted = cpops_prov_list
cpops_prov_list_sorted.sort()
print(f"* population -> {cpops_prov_list_sorted=} , length {len(cpops_prov_list_sorted)}")
print(f"* Do we get the same areas from Covid Data and Population data: {cpops_prov_list_sorted==unique_provinces}")

# sort by date
c2 = c1.sort_values(by=["date"])

# show results of final data frame before plotting
print()
pd_quick_info_maybe_save(c2, "FINAL DATA", covid_csv_final)

#################################################
#                     PLOT                      #
#################################################

# plot
covid_init_and_plot(c2,cpop_list,filename_prefix,plot_title,[ "date", "area", "cases", "deaths", "new_cases", "new_deaths" ],visible_provinces,to_get_to_root="..",DEBUGAREA="")

##### END #####
