#!/usr/bin/env python3

# Copyright (c) Huan He (He.Huan@mayo.edu)
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import pathlib
import itertools
from functools import reduce

###############################################################################
# Folders and filenames
###############################################################################
# the calculation version
FOLDER_V2 = 'v2'
FOLDER_V3 = 'v3'

# current path
FULLPATH = pathlib.Path(__file__).parent.absolute()
# folder for source files
FOLDER_SRC = os.path.join(FULLPATH, '../data/src')
# folder for the parsed results
FOLDER_PRS = os.path.join(FULLPATH, '../data/prs')
# folder for the result files
FOLDER_RST = os.path.join(FULLPATH, '../data/rst')
# folder for the raw data files
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')

# source folder for USAFacts
FOLDER_SRC_USAFACTS = os.path.join(
    FOLDER_SRC, 'usafacts'
)
# source folder for COVID Tracking
FOLDER_SRC_COVIDTRACKING = os.path.join(
    FOLDER_SRC, 'covidtracking'
)
# source folder for HSRC
FOLDER_SRC_HSRC = os.path.join(
    FOLDER_SRC, 'hsrc'
)
# so, need to save the raw file first
# unlike usafacts and ct, the JHU data files are splited by date
# source folder for JHU
FOLDER_SRC_JHU = os.path.join(
    FOLDER_SRC, 'jhu'
)
# the raw data for JHU
FOLDER_SRC_JHU_RAW = os.path.join(
    FOLDER_SRC_JHU, 'raw'
)
# unlike usafacts and ct, the CDCPVI data files are splited by date
# so, need to save the raw file first
# source folder for CDCPVI
FOLDER_SRC_CDCPVI = os.path.join(
    FOLDER_SRC, 'cdcpvi'
)
# the raw data for CDCPVI
FOLDER_SRC_CDCPVI_RAW = os.path.join(
    FOLDER_SRC_CDCPVI, 'raw'
)
# source folder for CDCVAC
FOLDER_SRC_CDCVAC = os.path.join(
    FOLDER_SRC, 'cdcvac'
)
# the raw data for CDCVAC
FOLDER_SRC_CDCVAC_RAW = os.path.join(
    FOLDER_SRC_CDCVAC, 'raw'
)
# the raw data for JHUCCI
FOLDER_SRC_JHUCCI_VAX = os.path.join(
    FOLDER_SRC, 'jhucci_vax'
)
# source folder for ACTNOW
FOLDER_SRC_ACTNOW = os.path.join(
    FOLDER_SRC, 'actnow'
)
# source folder for NYTimes
FOLDER_SRC_NYTIMES = os.path.join(
    FOLDER_SRC, 'nytimes'
)
# source folder for Our World in Data
FOLDER_SRC_OWIDVAC = os.path.join(
    FOLDER_SRC, 'owidvac'
)

# result folder for v2
FOLDER_RST_V2 = os.path.join(FOLDER_RST, 'v2')
# result folder for v3
FOLDER_RST_V3 = os.path.join(FOLDER_RST, 'v3')

# the last update time file
FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')

# the population data file
FN_WORLD_POPU = os.path.join(FOLDER_RAW, 'world-population.csv')
FN_STATE_POPU = os.path.join(FOLDER_RAW, 'usstate-population.csv')
FN_COUNTY_POPU = os.path.join(FOLDER_RAW, 'uscnty-population.csv')

# the name and geo-location data file
FN_STATE_GEO = os.path.join(FOLDER_RAW, 'usstate-name-geo.csv')
FN_COUNTY_GEO = os.path.join(FOLDER_RAW, 'uscnty-name-geo.csv')

###############################################################################
# Source data save folders
###############################################################################

# the USAFacts county-level covid data
FN_SAVE_USAFACTS_COUNTY_COVID_DATA = os.path.join(
    FOLDER_SRC_USAFACTS, 'county_covid_data_%s.csv'
)
# the USAFacts county-level death data
FN_SAVE_USAFACTS_COUNTY_DEATH_DATA = os.path.join(
    FOLDER_SRC_USAFACTS, 'county_death_data_%s.csv'
)
# the COVID-19 Tracking state-level all data
FN_SAVE_COVIDTRACKING_STATE_DATA = os.path.join(
    FOLDER_SRC_COVIDTRACKING, 'state_data_%s.csv'
)
# the COVID-19 Tracking US-level all data
FN_SAVE_COVIDTRACKING_USA_DATA = os.path.join(
    FOLDER_SRC_COVIDTRACKING, 'usa_data_%s.csv'
)
# the HSR cluster county-level flag and prediction data
FN_SAVE_HSRC_COUNTY_COVID_DATA = os.path.join(
    FOLDER_SRC_HSRC, 'county_data_%s.csv'
)
# the HSR cluster state-level flag and prediction data
FN_SAVE_HSRC_STATE_COVID_DATA = os.path.join(
    FOLDER_SRC_HSRC, 'state_data_%s.csv'
)
# the HSR cluster state-level flag and prediction data
FN_SAVE_HSRC_STATE_COVID_DATA = os.path.join(
    FOLDER_SRC_HSRC, 'state_data_%s.csv'
)
# the JHU state-level raw data
FN_SAVE_JHU_STATE_RAW_DATA = os.path.join(
    FOLDER_SRC_JHU_RAW, 'state_raw_data_%s.csv'
)
# the JHU state-level data
FN_SAVE_JHU_STATE_ALL_DATA = os.path.join(
    FOLDER_SRC_JHU, 'state_data_%s.csv'
)
# the JHU world-level raw data
FN_SAVE_JHU_WORLD_RAW_DATA = os.path.join(
    FOLDER_SRC_JHU_RAW, 'world_raw_data_%s.csv'
)
# the JHU world-level data
FN_SAVE_JHU_WORLD_ALL_DATA = os.path.join(
    FOLDER_SRC_JHU, 'world_data_%s.csv'
)
# the JHU world-level ts case data
FN_SAVE_JHU_WORLD_TS_COVID_DATA = os.path.join(
    FOLDER_SRC_JHU, 'world_ts_covid_data_%s.csv'
)
# the JHU world-level ts death data
FN_SAVE_JHU_WORLD_TS_DEATH_DATA = os.path.join(
    FOLDER_SRC_JHU, 'world_ts_death_data_%s.csv'
)
# The CDCPVI raw usa data
FN_SAVE_CDCPVI_USA_RAW_DATA = os.path.join(
    FOLDER_SRC_CDCPVI_RAW, 'allusa_raw_data_%s.csv'
)
# the CDCPVI rst usa data
FN_SAVE_CDCPVI_USA_RST_DATA = os.path.join(
    FOLDER_SRC_CDCPVI_RAW, 'allusa_rst_data_%s.csv'
)
# The CDCPVI all usa data
FN_SAVE_CDCPVI_USA_ALL_DATA = os.path.join(
    FOLDER_SRC_CDCPVI, 'allusa_data_%s.csv'
)
# the CDCVAC raw state data, JSON format!
FN_SAVE_CDCVAC_STATE_VAC_RAW_DATA = os.path.join(
    FOLDER_SRC_CDCVAC_RAW, 'state_vac_raw_data_%s.json'
)
# the CDCVAC state vac data
FN_SAVE_CDCVAC_STATE_VAC_DATA = os.path.join(
    FOLDER_SRC_CDCVAC, 'state_vac_data_%s.csv'
)
# the JHUCCI VAX data
FN_SAVE_JHUCCI_STATE_VAX_DATA = os.path.join(
    FOLDER_SRC_JHUCCI_VAX, 'state_vax_data_%s.csv'
)
# for the ACT NOW
FN_SAVE_ACTNOW_STATE_DATA = os.path.join(
    FOLDER_SRC_ACTNOW, 'state_data_%s.csv'
)
FN_SAVE_ACTNOW_COUNTY_DATA = os.path.join(
    FOLDER_SRC_ACTNOW, 'county_data_%s.csv'
)
# for the NYTimes
FN_SAVE_NYTIMES_USA_DATA = os.path.join(
    FOLDER_SRC_NYTIMES, 'usa_data_%s.csv'
)
FN_SAVE_NYTIMES_STATE_DATA = os.path.join(
    FOLDER_SRC_NYTIMES, 'state_data_%s.csv'
)
FN_SAVE_NYTIMES_COUNTY_DATA = os.path.join(
    FOLDER_SRC_NYTIMES, 'county_data_%s.csv'
)
# the our world in data world-level vaccination data
FN_SAVE_OWIDVAC_WORLD_VAC_DATA = os.path.join(
    FOLDER_SRC_OWIDVAC, 'world_vac_data_%s.csv'
)

# the output JSON file for front end
FN_OUTPUT_STATE = '%s-history.json'
FN_OUTPUT_USA = 'US-history.json'
FN_OUTPUT_WORLD = 'WORLD-history.json'
FN_OUTPUT_MCHRR = 'MCHRR-history.json'

###############################################################################
# Data source URLS
###############################################################################
# data source of NYTimes
DS_NYTIMES_LATEST_USA = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us.csv"
DS_NYTIMES_LATEST_STATE = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us-states.csv"
DS_NYTIMES_LATEST_COUNTY = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us-counties.csv"
DS_NYTIMES_TS_USA = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv"
DS_NYTIMES_TS_STATE = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
DS_NYTIMES_TS_COUNTY = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"

# data source of COVID Act Now
DS_ACTNOW_API_KEY = '8932dc019a28465dac03c8adc2965ffe'
DS_ACTNOW_LATEST_STATE = "https://api.covidactnow.org/v2/states.csv?apiKey=%s" % DS_ACTNOW_API_KEY
DS_ACTNOW_LATEST_COUNTY = "https://api.covidactnow.org/v2/counties.csv?apiKey=%s" % DS_ACTNOW_API_KEY
DS_ACTNOW_TS_STATE = 'https://api.covidactnow.org/v2/states.timeseries.csv?apiKey=%s' % DS_ACTNOW_API_KEY
DS_ACTNOW_TS_COUNTY = 'https://api.covidactnow.org/v2/counties.timeseries.csv?apiKey=%s' % DS_ACTNOW_API_KEY

# data source of USAFacts
DS_USAFACTS_CONFIRM = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv'
DS_USAFACTS_DEATH = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv'

# data source of COVID-19 Tracking
DS_COVIDTRACKING_STATE = 'https://covidtracking.com/data/download/all-states-history.csv'
DS_COVIDTRACKING_USA = 'https://covidtracking.com/data/download/national-history.csv'

# data source of HSR cluster push
DS_HSRC_COUNTY = '/data/covid19/public_web_county_data_%s.csv'
DS_HSRC_STATE = '/data/covid19/public_web_state_data_%s.csv'

# data source of JHU repo
DS_JHU_WORLD_DAILY = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/%s.csv"
DS_JHU_STATE_DAILY = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/%s.csv"
DS_JHU_WORLD_TS_CONFIRMED = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
DS_JHU_WORLD_TS_DEATH = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
DS_JHU_WORLD_TS_RECOVER = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
# data source of the JHU Centers for Civic Impact
DS_JHUCCI_VAX_USA = "https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/raw_data/vaccine_data_us_state_timeline.csv"

# data source of the CDC PVI
# DS_CDCPVI_RAW_DATA = "https://raw.githubusercontent.com/COVID19PVI/data/master/Model11.2/Model_11.2_%s_data.csv"
# DS_CDCPVI_RST_DATA = "https://raw.githubusercontent.com/COVID19PVI/data/master/Model11.2/Model_11.2_%s_results.csv"
DS_CDCPVI_RAW_DATA = "https://raw.githubusercontent.com/COVID19PVI/data/master/Model11.2.1/data/Model_11.2.1_%s_data.csv"
DS_CDCPVI_RST_DATA = "https://raw.githubusercontent.com/COVID19PVI/data/master/Model11.2.1/Model_11.2.1_%s_results.csv"

# data source of the CDC Vaccine
DS_CDCVAC_STATE = 'https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=vaccination_data'

# data source of the world vaccine
DS_OWIDVAC_WORLD = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"

###############################################################################
# Parsing configs
###############################################################################

# CDT MAX CUT
CDT_CUT_VALUE = 100

# CDT smooth days
N_CDT_SMOOTH_DAYS = 4

# the number of days for the output JSON
N_DATES = 60

# for calculating CRC offset index
START_DATE_IDX = 14

# the number of prediction days for the output JSON
N_PRED_DATES = 14

# the number per capita base
N_PERCAPITA = 100000

# the flag for incomplete data
FLAG_INCOMPLETE_DATA = 1
FLAG_COMPLETE_DATA = 0

# Cr7d100k Green cut value 1, less or equal to this value is pGREEN
S_GREEN_CRP_CUT_VALUE_1 = 10

# Cr7d100k Green cut value 1, less or equal to this val for pGREEN
S_GREEN_RW_CUT_VALUE_2 = 1

# Cr7d100k Green cut value 2, less than this value
S_GREEN_CRP_CUT_VALUE_2 = 15

# Cr7d100k Red cut value 3, greater than this RW for pRED
S_RED_RW_CUT_VALUE_1 = 1.1

# Cr7d100k Red cut value 3, greater than this value and RW>1 is pRED
S_RED_CRP_CUT_VALUE_1 = 15

# Cr7d100k Red cut value 4, greater than this value is pRED
S_RED_CRP_CUT_VALUE_2 = 30


###############################################################################
# Other configs
###############################################################################

# for display
WIDTH_SEP_LINE = 80

# first date
FIRST_DATE = '2020-03-01'
FIRST_DATE_JHU = '2020-04-12'
FIRST_DATE_VAC = '2021-01-13'

# the NaN threshold for COVID act now state
# if the number of NaN states is greater than this value, skip updating
N_ACTNOW_NAN_STATES = 45


# MAYO CLINIC REGIONS
_mc_region_list = [
    dict(name='PHX', fips=(4005, 4017, 4013, 4007, 4009, 
                            4011, 4027, 4012)),
    dict(name='JAX', fips=(13191, 13127, 13037, 13065, 13049, 
                            13069, 13003, 13025, 13005, 13229,
                            12031, 12109 )),
    dict(name='RST', fips=(27037, 27043, 27131, 27169, 27157,
                            27139, 27109, 27045, 27047, 27039, 
                            27147, 27099, 27049, #27161, 
                            19189, 19195, # 55093, 
                            55011, 55091)),
    dict(name='SWWI', fips=(27055, 55063, 55081, 55123, 55121)),
    dict(name='SWMN', fips=(27013, 27103, 27015, 27063, 27091, 
                            27079, 27161, 27165)),
    dict(name='NWWI', fips=(55035, 55033, 55019, 55017, 55093, 
                            55005)),
]
_mc_region_list.append({
    "name": "AVG", 
    "fips": list(set(reduce(lambda a, b: { 'fips': a['fips'] + b['fips'] }, 
    _mc_region_list)['fips']))
})

MC_REGIONS = _mc_region_list
MC_HRR_COUNTIES_INT = list(itertools.chain(*[ r['fips'] for r in _mc_region_list ]))
MC_HRR_COUNTIES_5DS = [ '%05d' % v for v in MC_HRR_COUNTIES_INT ]