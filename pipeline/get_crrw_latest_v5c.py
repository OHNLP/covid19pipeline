#%% load packages
import os
import time
import math
import json
import random
import datetime
import dateutil
import pathlib
import argparse

from functools import reduce

from tqdm import tqdm

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst')
FOLDER_ARX = os.path.join(FULLPATH, '../data/arx')
FOLDER_SRC = os.path.join(FULLPATH, '../data/src')

FN_COUNTY = os.path.join(FOLDER_RAW, 'county_stat_data.csv')
FN_COUNTY_FIPS = os.path.join(FOLDER_RAW, 'uscnty-name-geo.csv')
FN_COUNTY_POPU = os.path.join(FOLDER_RAW, 'uscnty-population.csv')
FN_STATE_FIPS = os.path.join(FOLDER_RAW, 'usstate-name-geo.csv')
FN_STATE_POPU = os.path.join(FOLDER_RAW, 'usstate-population.csv')
FN_WORLD_POPU = os.path.join(FOLDER_RAW, 'world-population.csv')

# The data of USAFacts
FN_CNTY_USAFACTS_COVID_HIST = os.path.join(FOLDER_SRC, 'usafacts', 'uscnty-covid-%s.csv')
FN_CNTY_USAFACTS_DEATH_HIST = os.path.join(FOLDER_SRC, 'usafacts', 'uscnty-death-%s.csv')

# The data of PVI
FN_CNTY_CDCPVI_HIST = os.path.join(FOLDER_SRC, 'cdc', 'uscnty-cdcpvi-history.csv')

# the output!
FN_OUTPUT_CNTY_FC_HIST = os.path.join(FOLDER_RST, 'uscnty-fc-history.json')
FN_OUTPUT_CNTY_FC_HIST_STATE = os.path.join(FOLDER_RST, 'state', '%s-history.json')
FN_OUTPUT_STATE_FC_HIST = os.path.join(FOLDER_RST, 'state', 'US-history.json')
FN_OUTPUT_MC_FC_HIST = os.path.join(FOLDER_RST, 'mchrr-fc-history.json')
FN_OUTPUT_WORLD_FC_HIST = os.path.join(FOLDER_RST, 'world-fc-history.json')


# cut value for the CDT
CDT_CUT_VALUE = 100

# cut value for the new case ratio
CRT_CUT_VALUE = 5

# Cr7d100k Green cut value 1, less or equal to this value is pGREEN
S_GREEN_CRP_CUT_VALUE_1 = 10

# Cr7d100k Green cut value 2, less than this value
S_GREEN_CRP_CUT_VALUE_2 = 15

# Cr7d100k Red cut value 3, greater than this value and RW>1 is pRED
S_RED_CRP_CUT_VALUE_1 = 10

# Cr7d100k Red cut value 4, greater than this value is pRED
S_RED_CRP_CUT_VALUE_2 = 30

# last time update
FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')
print('* defined the filenames:')
for v in dir():
    if v.startswith('FN_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

# define data sources
# US-level data
DS_USAFACT_US_CONFIRMED = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv'
DS_USAFACT_US_DEATH = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv'
DS_NYT_US_CONFIRMED_DEATH = 'https://github.com/nytimes/covid-19-data/raw/master/us-counties.csv'
DS_COVIDTRACKING_STATE = 'https://covidtracking.com/api/v1/states/daily.csv'
# world-level data
DS_CSSE_WORLD_CONFIRMED = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
DS_CSSE_WORLD_DEATH = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
DS_CSSE_WORLD_RECOVER = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'

print('* defined the data sourcess:')
for v in dir():
    if v.startswith('DS_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

# dfine the switches
IS_PATCH_MDH_NUMBER = 'no'
IS_CREATE_ALL_HISTORY = 'no'
USE_THIS_COVID_CASE_DATA = 'no'
USE_THIS_COVID_DEATH_DATA = 'no'


# quick fix for the int64 not json serialization
# from https://stackoverflow.com/questions/50916422/python-typeerror-object-of-type-int64-is-not-json-serializable
class NpEncoder(json.JSONEncoder):
    """ Custom encoder for numpy data types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):

            return int(obj)

        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)

        elif isinstance(obj, (np.complex_, np.complex64, np.complex128)):
            return {'real': obj.real, 'imag': obj.imag}

        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()

        elif isinstance(obj, (np.bool_)):
            return bool(obj)

        elif isinstance(obj, (np.void)): 
            return None

        return json.JSONEncoder.default(self, obj)

#%% the main part

def main(mode='all'):
    #%% Load county level data
    print("""
    ###############################################################
    # Get US County Data from usafactsstatic.blob.core.windows.net
    ###############################################################
    """)
    county_data = pd.read_csv(FN_COUNTY)

    if USE_THIS_COVID_CASE_DATA != 'no':
        covid_data = pd.read_csv(USE_THIS_COVID_CASE_DATA)
        print('* loaded specific covid cases data: %s' % USE_THIS_COVID_CASE_DATA)
    else:
        covid_data = pd.read_csv(DS_USAFACT_US_CONFIRMED)
        print('* loaded USAFACT covid confirmed data')

    if USE_THIS_COVID_DEATH_DATA != 'no':
        death_data = pd.read_csv(USE_THIS_COVID_DEATH_DATA)
        print('* loaded specific covid death data: %s' % USE_THIS_COVID_DEATH_DATA)
    else:
        death_data = pd.read_csv(DS_USAFACT_US_DEATH)
        print('* loaded USAFACT covid death data')

    # 9/1/2020: add world data
    confirmed_df = pd.read_csv(DS_CSSE_WORLD_CONFIRMED)
    deaths_df = pd.read_csv(DS_CSSE_WORLD_DEATH)
    confirmed_df = confirmed_df.groupby(['Country/Region']).sum()
    deaths_df = deaths_df.groupby(['Country/Region']).sum()
    confirmed_df.reset_index(inplace=True)
    deaths_df.reset_index(inplace=True)
    # give alia name
    covid_data_world = confirmed_df
    death_data_world = deaths_df
    print('* loaded worldata into %s lines' % len(confirmed_df))

    # 7/28/2020: add state name
    state_geo_data = pd.read_csv(FN_STATE_FIPS)
    state_dict = {}
    for idx, row in state_geo_data.iterrows():
        fips = row['stateFIPS']
        abbr = row['stateAbbr']
        name = row['stateName']

        obj = {
            'FIPS': fips,
            'state': abbr,
            'name': name
        }

        state_dict[fips] = obj
        state_dict[abbr] = obj
    print('* loaded state geo data and created dict')

    # 9/10/2020: add PVI data
    cdcpvi_df = pd.read_csv(FN_CNTY_CDCPVI_HIST)
    
    # 11/12/2020: fix the NaN in output JSON
    cdcpvi_df.fillna(0, inplace=True)
    print('* loaded CDC PVI data, the latest is %s' % cdcpvi_df.columns[-1])

    # get the state level PVI
    cdcpvi_state_data = cdcpvi_df[:]
    cdcpvi_state_data['stateFIPS'] = cdcpvi_state_data['countyFIPS'] // 1000
    cdcpvi_state_data = cdcpvi_state_data.groupby('stateFIPS').median()
    cdcpvi_state_data.reset_index(inplace=True)
    cdcpvi_state_data['stateFIPS'] = cdcpvi_state_data['stateFIPS'].astype(int)

    # convert the cdcpvi to abbr-index
    cdcpvi_state_data['state'] = cdcpvi_state_data.apply(lambda r: state_dict[int(r['stateFIPS'])]['state'], axis=1)
    cdcpvi_state_data.set_index('state', inplace=True)

    # 11/12/2020, fix the NaN in output in state level
    cdcpvi_state_data.fillna(0, inplace=True)
    print('* get median of counties as state PVI')

    # 7/25/2020: add covidtracking.com data
    track_data = pd.read_csv(DS_COVIDTRACKING_STATE)

    # 07/01/2020: fix column name error!!!
    # how this unamed comes?
    cols_rm = []
    for col in covid_data.columns:
        if col.startswith('Unnamed'):
            cols_rm.append(col)
    if len(cols_rm) > 0:
        covid_data.drop(columns=cols_rm, inplace=True)
        print('* removed error name columns in covid_data: %s' % cols_rm)
    else:
        print('* no error name columns in covid_data')

    cols_rm = []
    for col in death_data.columns:
        if col.startswith('Unnamed'):
            cols_rm.append(col)
    if len(cols_rm) > 0:
        death_data.drop(columns=cols_rm, inplace=True)
        print('* removed error name columns in death_data: %s' % cols_rm)
    else:
        print('* no error name columns in death_data')

    # then last column should be the date
    # and save this 
    last_col = covid_data.columns[-1]
    dt = dateutil.parser.parse(last_col)
    dt_fn = dt.strftime('%Y-%m-%d')
    fn = os.path.join(FN_CNTY_USAFACTS_COVID_HIST % dt_fn)

    covid_data.to_csv(fn)
    print("* saved %s covid_data to %s" % (last_col, fn))

    last_col = death_data.columns[-1]
    dt = dateutil.parser.parse(last_col)
    dt_fn = dt.strftime('%Y-%m-%d')
    fn = os.path.join(FN_CNTY_USAFACTS_DEATH_HIST % dt_fn)
    death_data.to_csv(fn)
    print("* saved %s death_data to %s" % (last_col, fn))

    covid_data.set_index('countyFIPS', inplace=True)
    county_data.set_index('countyFIPS', inplace=True)

    # 12/15/2020: why NA???
    death_data = death_data.dropna()

    # 11/18/2020: why empty fips????
    death_data = death_data.loc[death_data['countyFIPS']!=' ', :]
    death_data['countyFIPS'] = death_data['countyFIPS'].apply(lambda v: int(v))
    death_data.set_index('countyFIPS', inplace=True)

    
    # 11/08/2020: apply fix on death data to Hennepin, MN
    new_val = 1020
    old_val = death_data.loc[27053, '11/7/20']
    death_data.loc[27053, '11/7/20'] = new_val
    print('* applied data fix (%s -> %s) to death data on 11/7/20 of Hennepin, MN' % (old_val, new_val))


    # quick fix for 12/07/2020
    covid_data.loc[37199, '12/7/20'] = 659
    print('* applied the data fix for 37199 county on 12/7/20 to %s' % covid_data.loc[37199, '12/7/20'])
    time.sleep(1)

    # rename column!!!
    # how can they change header date format!!!
    # rename the columns of covid data
    cols_need_rename = {
        'County Name': 'countyName'
    }
    for colname in covid_data.columns:
        try:
            dt = dateutil.parser.parse(colname)
            new_colname = dt.strftime('%-m/%-d/%y')
            if new_colname != colname:
                cols_need_rename[colname] = new_colname
        except:
            print('* not date column: %s' % colname)
    covid_data.rename(columns=cols_need_rename, inplace=True)
    print('* renamed %s date cols in covid data' % len(cols_need_rename))

    # rename the columns of death_data
    cols_need_rename = {
        'County Name': 'countyName'
    }
    for colname in death_data.columns:
        try:
            dt = dateutil.parser.parse(colname)
            new_colname = dt.strftime('%-m/%-d/%y')
            if new_colname != colname:
                cols_need_rename[colname] = new_colname
        except:
            print('* not date column: %s' % colname)
    death_data.rename(columns=cols_need_rename, inplace=True)
    print('* renamed %s date cols in death data' % len(cols_need_rename))

    # quick fix for 4/15/2020
    # death_data['4/15/20'] = death_data['4/14/20']

    # fix na and convert date format

    # sum all the counties into state level data
    covid_data_state = covid_data.groupby('State').sum()
    death_data_state = death_data.groupby('State').sum()
    covid_data_state.drop(columns=['stateFIPS'], inplace=True)
    death_data_state.drop(columns=['stateFIPS'], inplace=True)
    print('* summed the state-level numbers')


    # sum all the states into USA level data
    covid_data_usa = pd.DataFrame(covid_data_state.sum()).T
    death_data_usa = pd.DataFrame(death_data_state.sum()).T
    print('* summed the usa-level numbers')

    # sum all the MC HRR regions
    mc_region_list = [
        dict(name='PHX', fips=(4005, 4017, 4013, 4007, 4009, 
                                4011, 4027, 4012)),
        dict(name='JAX', fips=(13191, 13127, 13037, 13065, 13049, 
                                13069, 13003, 13025, 13005, 13229,
                                12031, 12109 )),
        dict(name='RST', fips=(27037, 27043, 27131, 27169, 27157,
                                27139, 27109, 27045, 27047, 27039, 
                                27147, 27161, 27099, 27049, 
                                19189, 19195, 
                                55011, 55093, 55091)),
        dict(name='SWWI', fips=(27055, 55063, 55081, 55123, 55121)),
        dict(name='SWMN', fips=(27013, 27103, 27015, 27063, 27091, 
                                27079, 27161, 27165)),
        dict(name='NWWI', fips=(55035, 55033, 55019, 55017, 55093, 
                                55005)),
    ]
    # add an ALL MC HRR
    mc_region_list.append({
        "name": "AVG", 
        "fips": list(set(reduce(lambda a, b: { 'fips': a['fips'] + b['fips'] }, mc_region_list)['fips']))
    })
    covid_data_mchrr = []
    death_data_mchrr = []
    pop_data_mchrr = []
    pop_data = pd.read_csv(FN_COUNTY_POPU)
    pop_data.set_index('FIPS', inplace=True)

    for mcr in mc_region_list:
        tmp = pd.DataFrame(covid_data.loc[mcr['fips'], covid_data.columns[3:]].sum()).T
        tmp['region'] = mcr['name']
        tmp.set_index('region', inplace=True)
        covid_data_mchrr.append(tmp)

        tmp = pd.DataFrame(death_data.loc[mcr['fips'], death_data.columns[3:]].sum()).T
        tmp['region'] = mcr['name']
        tmp.set_index('region', inplace=True)
        death_data_mchrr.append(tmp)
        
        tmp = pd.DataFrame(pop_data.loc[mcr['fips'], ['POP']].sum()).T
        tmp['region'] = mcr['name']
        tmp.set_index('region', inplace=True)
        pop_data_mchrr.append(tmp)

    covid_data_mchrr = pd.concat(covid_data_mchrr)
    death_data_mchrr = pd.concat(death_data_mchrr)
    pop_data_mchrr = pd.concat(pop_data_mchrr)
    print('* summed the MC HRR region numbers')

    # remove the fips==0 lines since no county info related
    covid_data = covid_data.loc[covid_data.index>0, :]
    death_data = death_data.loc[death_data.index>0, :]
    print('* removed index=0 rows')
    print('* loaded data! %s covid, %s death' % (len(covid_data), len(death_data)))


    # 5/23/2020 updates
    # the death data may not be updated timely
    # so if merge, the latest won't be added _ncc suffix
    # therefore, use yesterday instead
    col_last1 = covid_data.columns[-1]
    col_last2 = covid_data.columns[-2]
    if col_last1 not in death_data.columns:
        death_data[col_last1] = death_data[col_last2]
        print('! %s NOT exists in death data, use %s instead!' % (col_last1, col_last2))
    else:
        print('* great, death data is aligned with covid data!')
    time.sleep(.888)


    #%% get cdt and basic stats
    print("""
    ###############################################################
    # US County Cases Doubling Time and Other
    ###############################################################
    """)
    col_last1 = covid_data.columns[-1]
    col_last2 = covid_data.columns[-2]

    # set the start date
    smooth_days = 4
    n_days_cut = 60

    start_date = '2/10/20'
    idx_start_date = covid_data.columns.values.tolist().index(start_date)
    col_lastns = covid_data.columns[idx_start_date:]
    n_days = len(covid_data.columns[idx_start_date:])
    col_ndays_ago = col_lastns[0]

    # smooth for the CDT
    dates_w4dm = covid_data.columns[-(n_days + smooth_days):]
    dates_frst = covid_data.columns[3:]

    print('* there will be %s days since %s to today' % (n_days, col_ndays_ago))
    print('* the last %s days will be used for display' % (n_days_cut))

    # prepare the virus test data
    states = track_data.state.unique().tolist()
    dates = list(filter(lambda v: v>20200125, track_data.date.unique()))

    tmp = track_data.fillna(0)
    track_data_usa = tmp.groupby(['date']).sum()
    track_data_usa.reset_index(inplace=True)
    track_data_usa['state'] = 'US'

    track_data_all = pd.concat([track_data_usa, track_data])
    df_track = track_data_all.set_index(['date', 'state'])
    states.append('US')

    print('* created df_track raw data [%s - %s]' % (dates[0], dates[-1]))

    # this is for the state level test data
    track_data_state = []
    # this is for the state level ncc and dth
    covid_data_state_tp = []
    death_data_state_tp = []
    print('* building virus test dataset and state level dataset')

    cnt_missing = 0
    for state in tqdm(states):
        dd = {'state': state}

        # for building an obj for state level ncc and dth
        dd_c = {'state': state }
        dd_d = {'state': state }

        total_tests = []
        positives = []
        recovereds = []
        deaths = []

        for i, dt in enumerate(dates_frst):
            tmp = dt.split('/')
            y = 2000 + int(tmp[2])
            m = int(tmp[0])
            d = int(tmp[1])
            date = int('%d%02d%02d' % (y, m, d))

            # get values
            try:
                row = df_track.loc[(date, state)]
                total_test = row['totalTestResults']
                positive = row['positive']
                recovered = row['recovered']
                death = row['death']
            except:
                if i == 0:
                    total_test = 0
                    positive = 0
                    recovered = 0
                    death = 0
                else:
                    total_test = total_tests[-1]
                    positive = positives[-1]
                    recovered = recovereds[-1]
                    death = deaths[-1]
                cnt_missing += 1
                # print(' - missing data %s for %s' % (date, state))
            total_tests.append(total_test)
            positives.append(positive)
            recovereds.append(recovered)
            deaths.append(death)

            if total_test == 0:
                tpr = 0
                rcr = 0
                dtr = 0
            else:
                tpr = positive / total_test
                rcr = 0 if positive == 0 else recovered / positive
                dtr = 0 if positive == 0 else death / positive

            dd['%s_total_test' % dt] = total_test
            dd['%s_total_positive' % dt] = positive
            dd['%s_total_recovered' % dt] = recovered
            dd['%s_total_death' % dt] = death
            dd['%s_tpr' % dt] = tpr
            dd['%s_rcr' % dt] = rcr
            dd['%s_dtr' % dt] = dtr

            dd_c['%s' % dt] = positive
            dd_d['%s' % dt] = death

        track_data_state.append(dd)
        covid_data_state_tp.append(dd_c)
        death_data_state_tp.append(dd_d)

    print('\n')

    track_data_state = pd.DataFrame(track_data_state)
    track_data_state.set_index('state', inplace=True)

    covid_data_state_tp = pd.DataFrame(covid_data_state_tp)
    death_data_state_tp = pd.DataFrame(death_data_state_tp)

    covid_data_state_tp.set_index('state', inplace=True)
    death_data_state_tp.set_index('state', inplace=True)

    covid_data_usa_tp = covid_data_state_tp.loc[['US']]
    death_data_usa_tp = death_data_state_tp.loc[['US']]

    print('* created track_data_state,covid_data_state_tp, death_data_state_tp')
    print('* found %s missing records related to dates' % (cnt_missing))

    # combine the USAFacts data and COVID Tracking data on state level
    covid_data_state_uftp = \
        pd.concat([
            covid_data_state, 
            covid_data_state_tp.loc[['AS', 'GU', 'MP', 'PR', 'VI'], :]
        ])
    death_data_state_uftp = \
        pd.concat([
            death_data_state, 
            death_data_state_tp.loc[['AS', 'GU', 'MP', 'PR', 'VI'], :]
        ])
    print('* created covid_data_state_uftp and death_data_state_uftp %s - %s' % (
        covid_data_state_uftp.columns[0],
        covid_data_state_uftp.columns[-1],
    ))

    #%% the main loop on county / state / USA level
    # make a copy and do everything on this copy

    # the county 
    dft_county = covid_data[:]

    # the state level
    # covid_data_state: only 51 states (50 + DC) from USAFacts
    # covid_data_state_tp: 56 states (50 + DC + 5 territories) from COVID Tracking
    # covid_data_state_uftp: 56 states (50 + DC from USAFacts + 5 terriest from COVID Tracking)
    # dft_state = covid_data_state[:]
    dft_state = covid_data_state_tp[:]
    # dft_state = covid_data_state_uftp[:]

    # the USA level
    dft_usa = covid_data_state_tp.loc[['US']]

    # the MC HRR level
    dft_mc = covid_data_mchrr[:]

    # the world level
    dft_world = covid_data_world[:]

    # decide which df to be included in calculation
    dfts = []
    if mode == 'world' or mode == 'all':
        dfts.append( ('world', dft_world) )
    if mode == 'county' or mode == 'all':
        dfts.append( ('county', dft_county) )
    if mode == 'state' or mode == 'all':
        dfts.append( ('state', dft_state) )
    if mode == 'usa' or mode == 'all':
        dfts.append( ('usa', dft_usa) )
    if mode == 'mc' or mode == 'all':
        dfts.append( ('mc', dft_mc) )

    # dfts = []
    # dfts.append( ('state', dft_state) )

    # calculate the metrics and prepare the all history data
    output_data_county = {}
    # split county level data by state
    output_data_county_by_state = {}
    # state data
    output_data_state = {}
    # USA data
    output_data_usa = {}
    # MC HRR data
    output_data_mc = {}
    # World data
    output_data_world = {}

    def _crrw_clr(v):
        if v <= 7: return 'G'
        if v >= 21: return 'R'
        return 'Y'

    for _ in dfts:
        level, dft = _[0], _[1]   
        # merge with the geo data
        if level == 'county':
            tmp = pd.read_csv(FN_COUNTY_FIPS)
            tmp.set_index('countyFIPS', inplace=True)
            dft = dft.merge(tmp.loc[:, ['lat', 'lon']], 
                left_index=True, right_index=True)

            # merge with the population data
            tmp = pd.read_csv(FN_COUNTY_POPU)
            tmp.set_index('FIPS', inplace=True)
            dft = dft.merge(tmp.loc[:, ['POP']],
                left_index=True, right_index=True)

            # merge with the death data
            dft = dft.merge(death_data.loc[:, death_data.columns[3:]], 
                left_index=True, right_index=True, suffixes=['_ncc', '_dth'])

            print('* added geo and population to county data')

        elif level == 'state':
            # merge with the population data
            tmp = pd.read_csv(FN_STATE_POPU)
            tmp = tmp[tmp['FIPS']!=0]
            tmp.set_index('ABBR', inplace=True)
            dft = dft.merge(tmp.loc[:, ['POP']],
                left_index=True, right_index=True)

            dft = dft.merge(death_data_state_uftp.loc[:, death_data_state_uftp.columns[:]], 
                left_index=True, right_index=True, suffixes=['_ncc', '_dth'])
            print('* added population to state data')
        elif level == 'usa':
            # merge with the population data
            tmp = pd.read_csv(FN_STATE_POPU)
            tmp = tmp[tmp['FIPS']==0]
            tmp.set_index('ABBR', inplace=True)
            dft = dft.merge(tmp.loc[:, ['POP']],
                left_index=True, right_index=True)
            
            dft = dft.merge(death_data_usa_tp.loc[:, death_data_usa_tp.columns[:]], 
                left_index=True, right_index=True, suffixes=['_ncc', '_dth'])
            print('* added population and death data to USA data')
        elif level == 'mc':
            tmp = pop_data_mchrr
            dft = dft.merge(tmp.loc[:, ['POP']], left_index=True, right_index=True)
            dft = dft.merge(death_data_mchrr.loc[:, death_data_mchrr.columns[:]], 
                left_index=True, right_index=True, suffixes=['_ncc', '_dth'])
            print('* added population and death data to MC HRR data')
        elif level == 'world':
            tmp = pd.read_csv(FN_WORLD_POPU)
            dft = dft.merge(tmp.loc[:, ['Name', 'Code', 'POP']], how='inner',
                left_on='Country/Region', right_on='Name')

            dft = dft.merge(death_data_world.loc[:, death_data_world.columns[:]], 
                left_on='Country/Region', right_on='Country/Region', suffixes=['_ncc', '_dth'])

            # set an index 
            dft['idx'] = dft['Code']
            dft.set_index('idx', inplace=True)
            print('* added population to world data')

        # set default values
        for dt in covid_data.columns[3:idx_start_date].tolist():
            dft[dt + '_cri'] = 0
            # fix ncc is NaN
            dft[dt + '_ncc'] = dft[dt + '_ncc'].fillna(0)
        print('* set the default value of cri as 0 before %s' % start_date)

        # do the math!
        print('* calculating the CDT and other metrics for %s' % level)
        for i in tqdm(range(smooth_days, len(dates_w4dm))):
            dt_today = dates_w4dm[i]
            dt_ystdy = dates_w4dm[i-1]
            dt_ndago = dates_w4dm[i-smooth_days]

            # to calculate the CrRW, we need to larger range of data
            idx_today = covid_data.columns.values.tolist().index(dt_today)
            dt_7dago = covid_data.columns[idx_today - 7]
            dt_7days = covid_data.columns[idx_today - 7: idx_today]
            dt_14dago = covid_data.columns[idx_today - 14]
            # print('* today: %s' % dt_today)

            # 7/23/2020, fix the data type error
            if is_numeric_dtype(dft[dt_today + '_ncc']):
                pass
            else:
                # show the error date
                print('* Non-numeric value in COVID data on %s %s' % (level, dt_today))
                dft.loc[:, dt_today + '_ncc'] = dft[dt_today + '_ncc'].astype('int64')

            # 11/08/2020, fix the data type error
            if is_numeric_dtype(dft[dt_today + '_dth']):
                pass
            else:
                # show the error date
                print('* Non-numeric value in DEATH data on %s %s' % (level, dt_today))
                try:
                    dft.loc[:, dt_today + '_dth'] = dft[dt_today + '_dth'].astype('int')
                except Exception as err:
                    print("* Couldn't ->int in DEATH data on %s %s" % (level, dt_today))
                    def __conv_str_to_int(v):
                        try:
                            v = int(v)
                        except:
                            print("* Found error %s in DEATH data on %s %s" % (v, level, dt_today))
                            v = 0
                        return v

                    dft.loc[:, dt_today + '_dth'] = dft[dt_today + '_dth'].apply(lambda v: __conv_str_to_int(v))
                    # usually cause by na value
                    # dft.loc[:, dt_today + '_dth'] = dft[dt_today + '_dth'].fillna(0)

            # fix ncc is NaN
            dft.loc[:, dt_today + '_ncc'] = dft.loc[:, dt_today + '_ncc'].fillna(0)

            # get the cdt
            dft.loc[:, dt_today + '_cdt'] = \
                smooth_days * np.log(2) / np.log((dft[dt_today + '_ncc'] + 0.5) / dft[dt_ndago + '_ncc'])
            
            # get the daily new cases DNC
            dft.loc[:, dt_today + '_dnc'] = \
                dft[dt_today + '_ncc'] - dft[dt_ystdy + '_ncc']
                
            # fix DNC < 0
            dft.loc[:, dt_today + '_dnc'] = dft[dt_today + '_dnc'].where( \
                ~(dft[dt_today + '_dnc']<0), 0)

            # fix DNC is NaN
            dft.loc[:, dt_today + '_dnc'] = dft.loc[:, dt_today + '_dnc'].fillna(0)

            # get the 7-day avg new cases per 100k
            dft.loc[:, dt_today + '_crp'] = \
                (dft[dt_today + '_ncc'] - dft[dt_7dago + '_ncc']) / dft['POP'] * 100000 / 7.0
            
            # fix 7-day new case rate per 100k is NaN
            dft.loc[:, dt_today + '_crp'] = dft.loc[:, dt_today + '_crp'].fillna(0)

            # round 7-day avg new case rate per 100k
            dft.loc[:, dt_today + '_crp'] = dft.loc[:, dt_today + '_crp'].round(2)

            # get the 7-day new case ratio
            dft.loc[:, dt_today + '_crt'] = \
                (dft[dt_today + '_ncc'] - dft[dt_7dago + '_ncc']) / ((dft[dt_7dago + '_ncc'] - dft[dt_14dago + '_ncc']))

            # fix the 7-day new case ratio NaN value
            dft.loc[:, dt_today + '_crt'] = dft.loc[:, dt_today + '_crt'].fillna(0)

            # fix the 7-day new case ratio Infinity value
            dft.loc[:, dt_today + '_crt'] = dft.loc[:, dt_today + '_crt'].replace([np.inf, -np.inf], CRT_CUT_VALUE)

            # round the 7-day new case ratio
            dft.loc[:, dt_today + '_crt'] = dft.loc[:, dt_today + '_crt'].round(2)

            # get crrw index 1 to 3, 
            # 1 is GREEN potential
            # 2 is YELLOW potential
            # 3 is RED potential
            # by default, set to YELLOW potential
            dft.loc[:, dt_today + '_cri'] = 2

            # apply GREEN potential
            # there are two cases
            # 1. if crp(Cr7d100k)<=1, it's safe from any level.
            # 2. if crp <=15 AND crt <=1, which means less cases, it's safe as well
            dft.loc[dft[dt_today + '_crp'] <=S_GREEN_CRP_CUT_VALUE_1, dt_today + '_cri'] = 1
            dft.loc[(dft[dt_today + '_crt']<=1) & (dft[dt_today + '_crp']<=S_GREEN_CRP_CUT_VALUE_2), dt_today + '_cri'] = 1

            # apply RED potential
            # there are two cases
            # 1. if crt > 1 and crp > 1, which means growing and the number of cases is high
            # 2. if crp > 30, no matter what, it's red
            dft.loc[(dft[dt_today + '_crt']>1) & (dft[dt_today + '_crp']>S_RED_CRP_CUT_VALUE_1), dt_today + '_cri'] = 3
            dft.loc[dft[dt_today + '_crp']>S_RED_CRP_CUT_VALUE_2, dt_today + '_cri'] = 3

            # get crrw cumulative value
            # of last 7 days cri
            dft.loc[:, dt_today + '_crv'] = \
                dft.loc[:, [ dt + '_cri' for dt in dt_7days.tolist() ]].sum(axis=1)

            # get crrw color
            dft.loc[:, dt_today + '_crc'] = \
                dft.loc[:, dt_today + '_crv'].apply(lambda v: _crrw_clr(v))

            # get the death rate
            dft.loc[:, dt_today + '_dtr'] = \
                dft[dt_today + '_dth'] / dft[dt_today + '_ncc']

            # get the ncc per 100k 
            dft.loc[:, dt_today + '_npp'] = \
                dft[dt_today + '_ncc'] / dft['POP'] * 100000

            # get the dnc per 100k 
            dft.loc[:, dt_today + '_dpp'] = \
                dft[dt_today + '_dnc'] / dft['POP'] * 100000

            #######################################################
            # fix error and outline values
            #######################################################

            # cut values
            dft.loc[:, dt_today + '_cdt'] = dft[dt_today + '_cdt'].where( \
                ~(dft[dt_today + '_cdt']>CDT_CUT_VALUE), CDT_CUT_VALUE)

            # fix CDT is 0
            dft.loc[:, dt_today + '_cdt'] = dft[dt_today + '_cdt'].where( \
                ~(dft[dt_today + '_cdt']==0), CDT_CUT_VALUE)

            # fix CDT is NaN
            dft.loc[:, dt_today + '_cdt'] = dft.loc[:, dt_today + '_cdt'].fillna(CDT_CUT_VALUE)

            # round CDT
            dft.loc[:, dt_today + '_cdt'] = dft.loc[:, dt_today + '_cdt'].round(2)

            # fix death is NaN
            dft.loc[:, dt_today + '_dth'] = dft.loc[:, dt_today + '_dth'].fillna(0)

            # fix death rate is Infinity
            dft.loc[:, dt_today + '_dtr'] = dft.loc[:, dt_today + '_dtr'].replace([np.inf, -np.inf], np.nan)

            # fix death rate is NaN
            dft.loc[:, dt_today + '_dtr'] = dft.loc[:, dt_today + '_dtr'].fillna(0)

            # round death rate
            dft.loc[:, dt_today + '_dtr'] = dft.loc[:, dt_today + '_dtr'].round(4)

            # fix ncc per 100,000 is NaN
            dft.loc[:, dt_today + '_npp'] = dft.loc[:, dt_today + '_npp'].fillna(0)

            # round ncc per 100,000
            dft.loc[:, dt_today + '_npp'] = dft.loc[:, dt_today + '_npp'].round(1)

            # fix dnc per 100,000 is NaN
            dft.loc[:, dt_today + '_dpp'] = dft.loc[:, dt_today + '_dpp'].fillna(0)

            # round dnc per 100,000
            dft.loc[:, dt_today + '_dpp'] = dft.loc[:, dt_today + '_dpp'].round(1)

        print('\n')

        cols_nccs = [ '%s_ncc'%v for v in dates_w4dm[smooth_days:].tolist() ]
        output_dates = dates_w4dm[smooth_days:]

        print('* building output json for %s level ...' % level)

        if level == 'county':
            dft_county = dft
        elif level == 'state':
            dft_state = dft
        elif level == 'usa':
            dft_usa = dft
        elif level == 'mc':
            dft_mc = dft
        elif level == 'world':
            dft_world = dft
        print('* bind dft to dft_%s obj' % level)

        for idxstr, row in tqdm(dft.iterrows()):
            if level == 'county':
                FIPS = '%s' % idxstr if idxstr > 9999 else '0%s' % idxstr
                countyName = covid_data.loc[idxstr, 'countyName']
                name = countyName.replace(' County', '')
                # fix for Washington D.C.
                if FIPS == '11001': name = "Washington, D.C."
                state = covid_data.loc[idxstr, 'State']
            elif level == 'state':
                state = idxstr
                FIPS = "%02d" % (state_dict[state]['FIPS'])
                name = state_dict[state]['name']
            elif level == 'usa':
                FIPS = '00'
                state = 'US'
                name = 'United States'
            elif level == 'mc':
                FIPS = idxstr
                state = {'PHX':'AZ', 'JAX':'FL', 'RST':'MN',
                        'SWWI':'WI', 'SWMN':'MN', 'NWWI':'WI',
                        'AVG': 'MN'}[idxstr]
                name = idxstr
            elif level == 'world':
                # FIPS here is the country code
                # e.g., United State is USA, China is CHN, United Kindom is GBR
                FIPS = row['Code']
                state = row['Code']
                name = row['Name']
            else:
                # well ... this won't happen?
                FIPS = idxstr
                state = idxstr
                name = idxstr

            # prepare output data
            obj = {
                'state': state,
                'FIPS': FIPS,
                'pop': row['POP'],
                'name': name,
                'cdts': row[[ dt + '_cdt' for dt in output_dates ]].tolist(),
                'nccs': row[[ dt + '_ncc' for dt in output_dates ]].tolist(),
                'npps': row[[ dt + '_npp' for dt in output_dates ]].tolist(),
                'dncs': row[[ dt + '_dnc' for dt in output_dates ]].tolist(),
                'dpps': row[[ dt + '_dpp' for dt in output_dates ]].tolist(),
                'dths': row[[ dt + '_dth' for dt in output_dates ]].tolist(),
                'dtrs': row[[ dt + '_dtr' for dt in output_dates ]].tolist(),
                'crps': row[[ dt + '_crp' for dt in output_dates ]].tolist(),
                'crts': row[[ dt + '_crt' for dt in output_dates ]].tolist(),
                'crcs': row[[ dt + '_crc' for dt in output_dates ]].tolist(),
                # use 0 as defult PVI
                'pvis': [0 for _ in output_dates ]
            }

            # add to dict
            if level == 'county':
                # add county data
                obj['lat'] = row['lat']
                obj['lon'] = row['lon']

                # add real PVI from the pvi_df
                intFIPS = int(FIPS)
                cdcpvi_data = cdcpvi_df[:]
                cdcpvi_data.set_index('countyFIPS', inplace=True)
                for _i, _dt in enumerate(output_dates):
                    try:
                        tmp = cdcpvi_data.loc[intFIPS, _dt]
                        obj['pvis'][_i] = round(tmp, 4)
                    except Exception as err:
                        print('* Err when parsing %s PVI, %s on %s, so use 0 instead' % (FIPS, err, _dt))

                # add obj to all history
                output_data_county[FIPS] = obj

                # add obj to splited
                if state not in output_data_county_by_state: output_data_county_by_state[state] = {}
                output_data_county_by_state[state][FIPS] = obj

            elif level == 'mc':
                output_data_mc[FIPS] = obj

            elif level == 'world':
                output_data_world[FIPS] = obj

            elif level == 'state' or level == 'usa':
                # put other metrics for state level
                obj['tprs'] = track_data_state.loc[
                    state,
                    [ dt + '_tpr' for dt in output_dates ]
                ].tolist()

                obj['rcrs'] = track_data_state.loc[
                    state,
                    [ dt + '_rcr' for dt in output_dates ]
                ].tolist()

                # put median PVI for this state
                # several regions have no PVI data
                if state in cdcpvi_state_data.index:
                    for _i, _dt in enumerate(output_dates):
                        try:
                            tmp = cdcpvi_state_data.loc[state, _dt]
                            obj['pvis'][_i] = round(tmp, 4)
                        except Exception as err:
                            print('* Err when parsing %s PVI, %s on %s, so use 0 instead' % (state, err, _dt))
                            
                # dd['%s_total_test' % dt] = total_test
                # dd['%s_total_positive' % dt] = positive
                # dd['%s_total_recovered' % dt] = recovered

                # 7/28/2020: add other metrics
                obj['ttrs'] = track_data_state.loc[
                    state,
                    [ dt + '_total_test' for dt in output_dates ]
                ].tolist()

                obj['tpts'] = track_data_state.loc[
                    state,
                    [ dt + '_total_positive' for dt in output_dates ]
                ].tolist()

                obj['trds'] = track_data_state.loc[
                    state,
                    [ dt + '_total_recovered' for dt in output_dates ]
                ].tolist()

                # fix na and round
                for attr in ['tprs', 'rcrs', 'ttrs', 'tpts', 'trds']:
                    for ix, v in enumerate(obj[attr]):
                        if pd.isna(v): 
                            if ix == 0:
                                obj[attr][ix] = 0
                            else:
                                obj[attr][ix] = obj[attr][ix-1]
                        if attr in ['tprs', 'rcrs']:
                            obj[attr][ix] = round(obj[attr][ix], 4)
                        else:
                            obj[attr][ix] = int(obj[attr][ix])
                
                # add state summary
                if level == 'state':
                    output_data_state[state] = obj
                else:
                    output_data_usa = obj
        print('\n')

    def _dconv(d):
        ps = d.split('/')
        return '20%s-%02d-%02d' % (ps[2], int(ps[0]), int(ps[1]))

    # create an all-in-one data object
    output_json = {
        'date': _dconv(col_last1),
        'dates': list(map(_dconv, dates_w4dm[smooth_days:].tolist())),
        'county_data': output_data_county,
        'state_data': output_data_state,
        'usa_data': output_data_usa
    }

    #%% output the all history data
    #########################################################
    # Output ALL-IN-ONE all history data
    #########################################################
    # json.dump(output_json, open(FN_OUTPUT_CNTY_FC_HIST, 'w'))
    # print('* saved %s days of json of CASES, CDT, DEATH, DEATH RATE data of all counties %s' % (n_days, FN_OUTPUT_CNTY_FC_HIST))


    #########################################################
    # Output ALL-IN-ONE all history data of MC HRR
    #########################################################
    output_json_mchrr = {
        'date': _dconv(col_last1),
        'dates': list(map(_dconv, dates_w4dm[smooth_days:].tolist())),
        'state_data': output_data_state,
        'usa_data': output_data_usa,
        'mc_data': output_data_mc
    }
    json.dump(output_json_mchrr, open(FN_OUTPUT_MC_FC_HIST, 'w'), cls=NpEncoder)
    print('* saved %s days of json of CASES, CDT, DEATH, DEATH RATE data of all MC HRR regions %s' % (n_days, FN_OUTPUT_CNTY_FC_HIST))


    #########################################################
    # Output ALL-IN-ONE all history data of World
    #########################################################
    output_json_world = {
        'date': _dconv(col_last1),
        'dates': list(map(_dconv, dates_w4dm[smooth_days:].tolist())),
        'world_data': output_data_world
    }
    json.dump(output_json_world, open(FN_OUTPUT_WORLD_FC_HIST, 'w'), cls=NpEncoder)
    print('* saved %s days of json of CASES, CDT, DEATH, DEATH RATE data of our WORLD %s' % (n_days, FN_OUTPUT_WORLD_FC_HIST))
    

    #%% output the splited all history data
    #########################################################
    # Output splited all history data
    #########################################################
    states = output_data_state.keys()

    for state in tqdm(states):
        fn = FN_OUTPUT_CNTY_FC_HIST_STATE % state
        if state in output_data_county_by_state:
            # most county has data
            tmp_county_data = {}
            for fips in output_data_county_by_state[state].keys():
                tmp_county_data[fips] = output_json['county_data'][fips]
        else:
            # for those 5 territories
            tmp_fips = '%s001' % output_data_state[state]['FIPS']
            tmp_data = output_json['state_data'][state]
            tmp_data['FIPS'] = tmp_fips
            tmp_county_data = {tmp_fips: tmp_data}

        state_output_json = {
            'geo': 'state',
            'date': output_json['date'],
            'dates': output_json['dates'],
            'state': state,
            'county_data': tmp_county_data,
            'state_data': output_json['state_data'][state],
            'usa_data': output_json['usa_data']
        }
        json.dump(state_output_json, open(fn, 'w'), cls=NpEncoder)
    print('\n')
    print('* saved splited all history data to %s files' % (len(states)))

    # all the 
    all_state_output_json = {
        'geo': 'country',
        'date': output_json['date'],
        'dates': output_json['dates'],
        'states': list(states),
        'state_data': output_json['state_data'],
        'usa_data': output_json['usa_data']
    }
    json.dump(all_state_output_json, open(FN_OUTPUT_STATE_FC_HIST, 'w'), cls=NpEncoder)
    print('* saved splited all history state data to %s' % (FN_OUTPUT_STATE_FC_HIST))


if __name__ == '__main__':
    main()
