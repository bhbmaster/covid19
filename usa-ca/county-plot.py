import pandas as pd
import numpy as np
import datetime
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import covid_init_and_plot, pd_quick_info_maybe_save # local module but up one directory hence the sys path append ..

### presetting pandas for correct stdout output ###

pd.set_option("max_colwidth", None)
# pd.set_option("max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

# prework

print("------------ preparing dataset -----------")
print()

### constants ###

SHOW_TOP_NUMBER=12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
csv_file = "CA-covid19cases_test.csv"
csv_file_parsable = "CA-covid19cases_test-parsable.csv"
filename_prefix = "county"
plot_title = "California Counties"

### ---- population stuff --- ###

# population file - NOTE: Now technically we don't need this as the information is in the CSV file
file_pop="county-pop.csv" # values from around 2020 good enough

# population file
cpops = pd.read_csv(file_pop,index_col="Rank")

# get top 10 (or SHOW_TOP_NUMBER) of counties based on population + select which ones to show enabled on legend
top10 = cpops.head(SHOW_TOP_NUMBER)["County"]
visible_counties = top10.values.tolist() # essentially its ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda', 'Sacramento', 'Contra Costa', 'Fresno', 'Kern', 'San Francisco']
visible_counties = ['Los Angeles', 'Santa Clara', 'San Mateo', 'San Francisco', '0-California-State']
print()
print(f"top counties={top10.values.tolist()}")
print(f"visible_counties={visible_counties}")
print()

# list of tuples [(county,pop) (county,pop)]
cpops_county_list=cpops["County"].values.tolist()
cpops_pop_list=cpops["Population"].values.tolist()
cpop_zip=zip(cpops_county_list,cpops_pop_list)
cpop_list=list(cpop_zip)
cpop_list.sort(key=lambda x:x[0]) # sort by first field county so alphabet

### ---- covid data stuff --- ###

# data input
# url_data="https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv" # after March 12 2021 this data is deprecated with new data at new site
# old data site https://data.ca.gov/dataset/covid-19-cases points to new site https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state
url_data="https://data.chhs.ca.gov/dataset/f333528b-4d38-4814-bebb-12db1f10f535/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a/download/covid19cases_test.csv" # NEW

# read in covid data for california counties
print("* downloading data 1/1")
c=pd.read_csv(url_data)
print("* downloading data complete")
print()

pd_quick_info_maybe_save(c, "RECEIVED DATA", csv_file)

# reformat data frame
def reformat_counties_data_frame_with_columns(c, cols):

    # c is the dataframe

    # cols is the columns we got to work with

    # ['date', 'area', 'area_type', 'population', 'cases', 'deaths', 'total_tests', 'positive_tests', 'reported_cases', 'reported_deaths', 'reported_tests'])
    #   0       1       2            3             4        5         6              7                 8                 9                  10

    DATE = cols[0]  # date or DATE
    AREA = cols[1]  # area or AREA
    AREA_TYPE = cols[2] # area_type or AREA_TYPE
    CASES = cols[4]  # cases or CASES
    DEATHS = cols[5] # deaths or DEATHS

    # first we sort the data by date
    c = c.sort_values(DATE,ascending=True)

    # Covid Data Manipulation to how we need the data

    cols_to_select=[DATE,AREA,AREA_TYPE,CASES,DEATHS]

    cleandates_c = c[c[DATE]!="NaN"]

    adjusted_cleaned_c = cleandates_c[cols_to_select]
    print()
    print(f"{adjusted_cleaned_c=}")
    print()

    # get list of all of the unique areas mentioned (counties and stuff)
    unique_areas = list(set(cleandates_c[AREA].values.tolist()))
    print()
    print(f"{unique_areas=}")
    print()

    # make new empty data frame we will add too
    cnew = pd.DataFrame(columns = [DATE,AREA,AREA_TYPE,CASES,DEATHS,"TOTALCASES","TOTALDEATHS"])

    for i, v in enumerate(unique_areas):
        print("** DEBUG: mini dataframe to create cumulative - ", i, v)
        cpart = adjusted_cleaned_c[adjusted_cleaned_c[AREA]==v]
        cpart = cpart.set_index(DATE)
        cpart["TOTALCASES"] = cpart[CASES].cumsum()
        cpart["TOTALDEATHS"] = cpart[DEATHS].cumsum()
        cpart = cpart.reset_index()
        print(cpart.tail())
        print()
        cnew = cnew.append(cpart, ignore_index = True)

    print("* DEBUG: put together a dataframe with cumulative columns")
    print(f"{cnew=}")

    # cols to select has been adjusted now
    cols_to_select=[DATE,AREA,AREA_TYPE,CASES,DEATHS,"TOTALCASES","TOTALDEATHS"]

    # Clean up - get counties only
    clean_county_c = cnew[cnew[AREA_TYPE]=="County"].dropna(subset=cols_to_select)
    print("* DEBUG: final clean counties")
    print(f"{clean_county_c=}")

    # GET CALIFORNIA STATE values out of the data as we want to show the whole states values too (there will be a county called 0-California-State which means its california duh)

    cali0 = cnew[cnew[AREA_TYPE]=="State"].dropna(subset=cols_to_select)

    clean_cali_c = cali0.replace("California","0-California-State")
    print("* DEBUG: final clean california")
    print(f"{clean_cali_c=}")

    # THE FINAL COMBINED DATA:
    final_c_and_cali = clean_county_c.append(clean_cali_c,ignore_index=True) # since indexes never got messed with this in these processes we can just remove ignore_index and keep its default as False but it doesn't hurt to keep
    # sidenote manually added in this line to county-pop.csv - whatever its not the prettiest i don't care: # 59,0-California-State,40129160
    # adding california in - finish

    # OKAY LETS SORT IT AND NOW ITS FINAL
    returnable_c = final_c_and_cali.sort_values(by=[DATE]) # sort by date

    print("* DEBUG: final clean california")
    print(returnable_c)

    # we are returning the date or DATE, area or AREA, cases or CASES, deaths or DEATHS, and modified dataframe c
    return DATE,AREA,CASES,DEATHS,returnable_c

# csv file columns sometimes come in lower case and sometimes upper case
try:
    # trying lower case and returning if date or DATE, area or AREA, cases or CASES, deaths or DEATHS, and modified c dataframe
    DATE, AREA, CASES, DEATHS, c = reformat_counties_data_frame_with_columns(c, ['date', 'area', 'area_type', 'population', 'cases', 'deaths',
       'total_tests', 'positive_tests', 'reported_cases', 'reported_deaths',
       'reported_tests'])
except:
    # trying upper case and returning if date or DATE, area or AREA, cases or CASES, deaths or DEATHS, and modified c dataframe
    DATE, AREA, CASES, DEATHS, c = reformat_counties_data_frame_with_columns(c, ['DATE', 'AREA', 'AREA_TYPE', 'POPULATUIB', 'CASES', 'DEATHS',
       'TOTAL_TESTS', 'POSITIVE_TESTS', 'REPORTED_CASES', 'REPORTED_DEATHS',
       'REPORTED_TESTS'])

print()
pd_quick_info_maybe_save(c, "FINAL PARSABLE DATA", csv_file_parsable)

###################################################
#              PLOTTING                           #
###################################################

# plot
covid_init_and_plot(c,cpop_list,filename_prefix,plot_title,[ DATE, AREA, "TOTALCASES", "TOTALDEATHS", CASES, DEATHS ],visible_counties,to_get_to_root="..",DEBUGAREA="")

##### END #####