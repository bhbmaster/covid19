import pandas as pd
import sys
sys.path.append("..")    # so we can import common from previous directory
from common import (  # local module but up one directory hence the sys path append ..
    covid_init_and_plot,
    pd_quick_info_maybe_save,
    pandas_display_options,
    read_csv_from_url,
    add_daily_diffs,
    CHHS_CA_CSV,
    CHHS_CA_PAGE,
    NYT_US_COUNTIES_CSV,
    NYT_US_STATES_CSV,
    NYT_COVID_REPO,
)

### presetting pandas for correct stdout output ###

pandas_display_options()
# pd.set_option("display.max_columns", None) # commented out to fix: pandas._config.config.OptionError: 'Pattern matched multiple keys'

# prework

print("------------ preparing dataset -----------")
print()

### constants ###

SHOW_TOP_NUMBER=12 # how many counties to have enabled when graph shows (others can be toggled on interactively)
csv_file = "CA-covid19cases_test.csv"
csv_file_parsable = "CA-covid19cases_test-parsable.csv"
filename_prefix = "county"
plot_title = "California Counties"
DROP_AREAS = {"Out of state", "Unknown"}

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

def format_chhs(raw):
    # CHHS columns have changed over time. Current file has daily + cumulative:
    # date, area, area_type, population, cases, cumulative_cases, deaths, cumulative_deaths, ...
    c = raw.copy()
    c.columns = [str(col).strip().lower() for col in c.columns]
    if "date" not in c.columns or "area" not in c.columns:
        raise ValueError(f"CHHS CSV missing expected columns: {list(c.columns)}")

    c["date"] = pd.to_datetime(c["date"], errors="coerce")
    c = c.dropna(subset=["date", "area"])
    c["date"] = c["date"].dt.strftime("%Y-%m-%d")

    if "cumulative_cases" in c.columns:
        c["TOTALCASES"] = pd.to_numeric(c["cumulative_cases"], errors="coerce")
        c["TOTALDEATHS"] = pd.to_numeric(c.get("cumulative_deaths"), errors="coerce")
        c["CASES"] = pd.to_numeric(c.get("cases"), errors="coerce")
        c["DEATHS"] = pd.to_numeric(c.get("deaths"), errors="coerce")
    else:
        # older CHHS dump: cases/deaths are daily only
        c["CASES"] = pd.to_numeric(c.get("cases"), errors="coerce").fillna(0)
        c["DEATHS"] = pd.to_numeric(c.get("deaths"), errors="coerce").fillna(0)
        c = c.sort_values(["area", "date"])
        c["TOTALCASES"] = c.groupby("area")["CASES"].cumsum()
        c["TOTALDEATHS"] = c.groupby("area")["DEATHS"].cumsum()

    c["CASES"] = c["CASES"].fillna(0)
    c["DEATHS"] = c["DEATHS"].fillna(0)
    c["TOTALCASES"] = c.groupby("area")["TOTALCASES"].ffill().fillna(0)
    c["TOTALDEATHS"] = c.groupby("area")["TOTALDEATHS"].ffill().fillna(0)

    area_type_col = "area_type" if "area_type" in c.columns else None
    if area_type_col:
        counties = c[c[area_type_col].astype(str).str.lower().eq("county")].copy()
        state = c[c[area_type_col].astype(str).str.lower().eq("state")].copy()
        state["area"] = state["area"].replace("California", "0-California-State")
        out = pd.concat([counties, state], ignore_index=True)
    else:
        out = c.copy()

    out = out[~out["area"].isin(DROP_AREAS)].copy()
    out = out[["date", "area", "CASES", "DEATHS", "TOTALCASES", "TOTALDEATHS"]]
    return out.sort_values(by=["date", "area"])

def format_nyt_california(counties_raw, states_raw):
    # NY Times us-counties.csv is the reliable historical archive (2020-01-25 through 2023-03-23)
    counties = counties_raw.copy()
    counties.columns = [str(col).strip().lower() for col in counties.columns]
    ca = counties[counties["state"].astype(str).eq("California")].copy()
    ca["date"] = pd.to_datetime(ca["date"], errors="coerce")
    ca = ca.dropna(subset=["date", "county"])
    ca["date"] = ca["date"].dt.strftime("%Y-%m-%d")
    ca["cases"] = pd.to_numeric(ca["cases"], errors="coerce").fillna(0)
    ca["deaths"] = pd.to_numeric(ca["deaths"], errors="coerce").fillna(0)
    ca = ca.rename(columns={"county": "area", "cases": "TOTALCASES", "deaths": "TOTALDEATHS"})
    ca = ca[~ca["area"].isin(DROP_AREAS)].copy()
    ca = add_daily_diffs(ca, "area", "date", "TOTALCASES", "TOTALDEATHS", new_cases_col="CASES", new_deaths_col="DEATHS")

    states = states_raw.copy()
    states.columns = [str(col).strip().lower() for col in states.columns]
    cali = states[states["state"].astype(str).eq("California")].copy()
    cali["date"] = pd.to_datetime(cali["date"], errors="coerce")
    cali = cali.dropna(subset=["date"])
    cali["date"] = cali["date"].dt.strftime("%Y-%m-%d")
    cali["area"] = "0-California-State"
    cali["TOTALCASES"] = pd.to_numeric(cali["cases"], errors="coerce").fillna(0)
    cali["TOTALDEATHS"] = pd.to_numeric(cali["deaths"], errors="coerce").fillna(0)
    cali = add_daily_diffs(cali, "area", "date", "TOTALCASES", "TOTALDEATHS", new_cases_col="CASES", new_deaths_col="DEATHS")

    out = pd.concat([
        ca[["date", "area", "CASES", "DEATHS", "TOTALCASES", "TOTALDEATHS"]],
        cali[["date", "area", "CASES", "DEATHS", "TOTALCASES", "TOTALDEATHS"]],
    ], ignore_index=True)
    return out.sort_values(by=["date", "area"])

print(f"* trying California source: CHHS {CHHS_CA_PAGE}")
used_source = "CHHS"
try:
    raw = read_csv_from_url(CHHS_CA_CSV)
    pd_quick_info_maybe_save(raw, "RECEIVED DATA", csv_file)
    c = format_chhs(raw)
    print("* using CHHS full historical county time series")
except Exception as e:
    print(f"* CHHS failed ({e})")
    print(f"* falling back to NY Times California counties archive {NYT_COVID_REPO}")
    used_source = "NY Times"
    counties_raw = read_csv_from_url(NYT_US_COUNTIES_CSV)
    states_raw = read_csv_from_url(NYT_US_STATES_CSV)
    pd_quick_info_maybe_save(counties_raw[counties_raw["state"].astype(str).eq("California")] if "state" in counties_raw.columns else counties_raw, "RECEIVED DATA", csv_file)
    c = format_nyt_california(counties_raw, states_raw)
    print("* using NY Times full historical California county archive")

print(f"* California source in use: {used_source}")
print(f"* date range: {c['date'].min()} through {c['date'].max()}")
print()

DATE, AREA, CASES, DEATHS = "date", "area", "CASES", "DEATHS"

# show results of final data frame before plotting
print()
pd_quick_info_maybe_save(c, "FINAL PARSABLE DATA", csv_file_parsable)

###################################################
#              PLOTTING                           #
###################################################

# plot
covid_init_and_plot(c,cpop_list,filename_prefix,plot_title,[ DATE, AREA, "TOTALCASES", "TOTALDEATHS", CASES, DEATHS ],visible_counties,to_get_to_root="..",DEBUGAREA="")

##### END #####
