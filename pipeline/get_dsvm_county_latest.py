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

print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst/dsvm')
FOLDER_ARX = os.path.join(FULLPATH, '../data/arx')

FN_COUNTY = os.path.join(FOLDER_RAW, 'county_stat_data.csv')
FN_COUNTY_FIPS = os.path.join(FOLDER_RAW, 'uscnty-name-geo.csv')
FN_COUNTY_POPU = os.path.join(FOLDER_RAW, 'uscnty-population.csv')

# minnesota MDH data
FN_MDH_MN_CASES = os.path.join(FOLDER_RAW, 'us-mn-cases.csv')
FN_MDH_MN_DEATHS = os.path.join(FOLDER_RAW, 'us-mn-deaths.csv')

FN_OUTPUT_COUNTY_CDT = os.path.join(FOLDER_RST, 'uscounty-cdt-latest.json')
FN_OUTPUT_COUNTY_DATA = os.path.join(FOLDER_RST, 'uscounty-data-latest.json')
FN_OUTPUT_COUNTY_DATA_HIS = os.path.join(FOLDER_RST, 'uscounty-data-history.json')

FN_OUTPUT_STATE_DATA = os.path.join(FOLDER_RST,  'usstate-data-latest.json')
FN_OUTPUT_STATE_DATA_HIS = os.path.join(FOLDER_RST, 'usstate-data-history.json')

CUT_VALUE = 100

# last time update
FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')
print('* defined the filenames:')
for v in dir():
    if v.startswith('FN_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

# define data sources
DS_USAFACT_US_CONFIRMED = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv'
DS_USAFACT_US_DEATH = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv'
DS_NYT_US_CONFIRMED_DEATH = 'https://github.com/nytimes/covid-19-data/raw/master/us-counties.csv'
DS_MDH_MN_ALL = 'https://www.health.state.mn.us/diseases/coronavirus/situation.html'

print('* defined the data sourcess:')
for v in dir():
    if v.startswith('DS_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

# dfine the switches
IS_MERGE_NYTIMES = 'no'
IS_PATCH_MDH_NUMBER = 'no'
IS_CREATE_ALL_HISTORY = 'no'
USE_THIS_COVID_CASE_DATA = 'no'
USE_THIS_COVID_DEATH_DATA = 'no'

#%% get the parameters for change algorithm
###############################################################
# Get some arguments
###############################################################
parser = argparse.ArgumentParser(description='Process the COVID-19 data.')

parser.add_argument("--IS_MERGE_NYTIMES", type=str, 
    choices=['yes', 'no', 'only_nytimes'], default='no',
    help="merge the data source from New York Time data source")
parser.add_argument("--IS_PATCH_MDH_NUMBER", type=str, 
    choices=['yes', 'no'], default='yes',
    help="use Minnesota Dep of Health data as patch")
parser.add_argument("--IS_CREATE_ALL_HISTORY", type=str, 
    choices=['yes', 'no'], default='no',
    help="create all the history data since 1/26/2020")

parser.add_argument("--USE_THIS_COVID_CASE_DATA", type=str, 
    default='no',
    help="use specificy covid case data")
parser.add_argument("--USE_THIS_COVID_DEATH_DATA", type=str, 
    default='no',
    help="use specificy covid death data")

args = parser.parse_args()
IS_MERGE_NYTIMES = args.IS_MERGE_NYTIMES
IS_PATCH_MDH_NUMBER = args.IS_PATCH_MDH_NUMBER
IS_CREATE_ALL_HISTORY = args.IS_CREATE_ALL_HISTORY
USE_THIS_COVID_CASE_DATA = args.USE_THIS_COVID_CASE_DATA
USE_THIS_COVID_DEATH_DATA = args.USE_THIS_COVID_DEATH_DATA

print('* defined and updated the switches:')
for v in dir():
    if v.startswith('IS_'):
        print('*   %s: %s' % (v, eval(v)))
print('')


#%% Load county level data
print("""
###############################################################
# Get US County Data from usafactsstatic.blob.core.windows.net
###############################################################
""")
county_data = pd.read_csv(FN_COUNTY)

if IS_MERGE_NYTIMES == 'yes':
    covid_nyt_data = pd.read_csv(DS_NYT_US_CONFIRMED_DEATH)
    print('* loaded NYTimes data')
    covid_nyt_data['fips'] = covid_nyt_data['fips'].fillna(0)
    covid_nyt_data['fips'] = covid_nyt_data['fips'].astype(int)
    covid_nyt_data['date2'] = pd.to_datetime(covid_nyt_data['date'])
    covid_nyt_data['date3'] = covid_nyt_data['date2'].apply(lambda r: r.strftime('%-m/%-d/%y'))
    covid_nyt_data.drop(columns=['date', 'date2'], inplace=True)
    covid_nyt_data.rename(columns={'date3': 'date'}, inplace=True)
    print('* fixed NA and date format in NYTimes data')
else:
    print('* ignored NY Times data')

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
last_col = covid_data.columns[-1]
last_col = last_col.replace('/', '_')
fn = os.path.join(FOLDER_ARX, 'covid_data_%s.csv' % last_col)
covid_data.to_csv(fn)
print("* saved %s covid_data to %s" % (last_col, fn))

last_col = death_data.columns[-1]
last_col = last_col.replace('/', '_')
fn = os.path.join(FOLDER_ARX, 'death_data_%s.csv' % last_col)
death_data.to_csv(fn)
print("* saved %s death_data to %s" % (last_col, fn))

covid_data.set_index('countyFIPS', inplace=True)
county_data.set_index('countyFIPS', inplace=True)
death_data.set_index('countyFIPS', inplace=True)

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

# apply the New York Times data as a patch
if IS_MERGE_NYTIMES == 'yes':
    print('* using nytimes data for correct missing!')
    # covid_data = pd.read_csv(os.path.join(FOLDER_RAW, 'covid_data_usafacts_04122020.csv'))

# apply the Minnesota Dep of Health as a patch
# if IS_PATCH_MDH_NUMBER == 'yes':
#     # get patch
#     df_patch_mdh_mn_cases = pd.read_csv(FN_MDH_MN_CASES, index_col='countyFIPS')
#     print('* loaded the MDH cases data until %s' % (
#         df_patch_mdh_mn_cases.columns[-1]
#     ))
#     df_patch_mdh_mn_deaths = pd.read_csv(FN_MDH_MN_DEATHS, index_col='countyFIPS')
#     print('* loaded the MDH deaths data until %s' % (
#         df_patch_mdh_mn_deaths.columns[-1]
#     ))

#     # apply the patch
#     covid_data.update(df_patch_mdh_mn_cases)
#     death_data.update(df_patch_mdh_mn_deaths)
#     print('* updated the covid_data and death_data with MDH data')

# remove the fips==0 lines
covid_data = covid_data.loc[covid_data.index>0, :]
death_data = death_data.loc[death_data.index>0, :]
print('* removed index=0 rows')

print('* loaded data! %s covid, %s death' % (len(covid_data), len(death_data)))

## fix wrong value!!!!
## how can the cases decrease!???
# cnt = 0
# for idx in covid_data.index:
#     # why FIPS == 0 can be used in this datashit!!!?
#     if idx == 0: continue
#     # why there is more than 1 records of sime FIPS???
#     if covid_data.loc[[idx], :]['stateFIPS'].count() > 1: continue
#     for i in range(5, len(covid_data.columns)):
#         col = covid_data.columns[i]
#         col_prev = covid_data.columns[i-1]
#         if covid_data.loc[idx, col] < covid_data.loc[idx, col_prev]:
#             cnt += 1
#             covid_data.loc[idx, col] = covid_data.loc[idx, col_prev]
# print('* refill %s cases in covid_data' % cnt)
patches = [
    [27053, [
        ['4/21/20', 1013],
        ['4/22/20', 1073],
        ['4/23/20', 1132],
        ['4/24/20', 1200],
        ['4/25/20', 1287],
        ['4/26/20', 1332],
        ['4/27/20', 1416],
        ['4/28/20', 1524]
    ]],
    # # Duval, FL
    # [12031, [
    #     ['7/22/20', 15747],
    #     ['7/23/20', 15752]
    # ]],
    # # St.Johns, FL
    # [12109, [
    #     ['7/22/20', 2612],
    #     ['7/23/20', 2669]
    # ]],
]
for patch in patches:
    for corr in patch[1]:
        covid_data.loc[patch[0], corr[0]] = corr[1]
        print('* %s %s -> %s' % (patch[0], corr[0], corr[1]))
    print('* added patch on %s' % patch[0])

print('* ')

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

#%% Compute US County Cases Doubling Time (CDT) and Rt
print("""
###############################################################
# US County Cases Doubling Time and Rt %s
###############################################################
""" % FN_OUTPUT_COUNTY_DATA)
col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]

# set the start date
n_days_cut = 30
start_date = '1/26/20'
idx_start_date = covid_data.columns.values.tolist().index(start_date)
col_lastns = covid_data.columns[idx_start_date:]
n_days = len(covid_data.columns[idx_start_date:])
col_ndays_ago = col_lastns[0]
print('* there will be %s days since %s to today' % (n_days, col_ndays_ago))
print('* the last %s days will be used for display' % (n_days_cut))

# smooth for the CDT
smooth_days = 4
cntyFIPSs = covid_data.index
dates_w4dm = covid_data.columns[-(n_days + smooth_days):]

# make a copy and do everything on this copy
dft = covid_data[:]

# merge with the geo data
tmp = pd.read_csv(FN_COUNTY_FIPS)
tmp.set_index('countyFIPS', inplace=True)
dft = dft.merge(tmp.loc[:, ['lat', 'lon']], 
    left_index=True, right_index=True)

# merge with the death data
dft = dft.merge(death_data.loc[:, death_data.columns[3:]], 
    left_index=True, right_index=True, suffixes=['_ncc', '_dth'])

dft.loc[99999, :] = dft.sum()

# do the math!
print('* calculating the CDT and SDR')
for i in tqdm(range(smooth_days, len(dates_w4dm))):
    dt_today = dates_w4dm[i]
    dt_ystdy = dates_w4dm[i-1]
    dt_ndago = dates_w4dm[i-smooth_days]
    # print('* today: %s' % dt_today)

    # get the cdt
    dft.loc[:, dt_today + '_cdt'] = \
        smooth_days * np.log(2) / np.log((dft[dt_today + '_ncc'] + 0.5) / dft[dt_ndago + '_ncc'])
    
    # get the new cases
    dft.loc[:, dt_today + '_new'] = \
        dft[dt_today + '_ncc'] - dft[dt_ystdy + '_ncc']

    # get the smoothed death rate
    dft.loc[:, dt_today + '_sdr'] = \
        ( dft[dt_today + '_dth'] - dft[dt_ndago + '_dth'] ) / \
        ( dft[dt_today + '_ncc'] - dft[dt_ndago + '_ncc'] + 0.5 )

    # cut values
    dft.loc[:, dt_today + '_cdt'] = dft[dt_today + '_cdt'].where( \
        ~(dft[dt_today + '_cdt']>CUT_VALUE), CUT_VALUE)

    # round CDT
    dft.loc[:, dt_today + '_cdt'] = dft.loc[:, dt_today + '_cdt'].round(2)

    # fix 0
    dft.loc[:, dt_today + '_cdt'] = dft[dt_today + '_cdt'].where( \
        ~(dft[dt_today + '_cdt']==0), CUT_VALUE)

    # fix s death rate
    dft.loc[:, dt_today + '_sdr'] = dft[dt_today + '_sdr'].where( \
        ~(dft[dt_today + '_sdr']>0.2), 0)

    # round s death rate
    dft.loc[:, dt_today + '_sdr'] = dft.loc[:, dt_today + '_sdr'].round(4)


# get the latest delta
dft.loc[:, col_last1 + '_d_cdt'] = dft[col_last1 + '_cdt'] - dft[col_last2 + '_cdt']
dft.loc[:, col_last1 + '_d_ncc'] = dft[col_last1 + '_ncc'] - dft[col_last2 + '_ncc']
dft.loc[:, col_last1 + '_d_dth'] = dft[col_last1 + '_dth'] - dft[col_last2 + '_dth']
dft.loc[:, col_last1 + '_d_sdr'] = dft[col_last1 + '_sdr'] - dft[col_last2 + '_sdr']

# fix death rate Nan
dft.loc[:, col_last1 + '_d_sdr'] = dft.loc[:, col_last1 + '_d_sdr'].fillna(0)

# calculate the Rt and prepare the all history data
output_data = {}
# print('* calculating the Rt')
cols_nccs = [ '%s_ncc'%v for v in dates_w4dm[smooth_days:].tolist() ]
for idxFIPS, row in tqdm(dft.iterrows()):
    FIPS = '%s' % idxFIPS if idxFIPS > 9999 else '0%s' % idxFIPS
    if idxFIPS == 99999:
        countyName = 'US'
        state = 'US'
    else:
        countyName = covid_data.loc[idxFIPS, 'countyName']
        state = covid_data.loc[idxFIPS, 'State']

    news = [ row[dt + '_new'] for dt in dates_w4dm[smooth_days:] ]

    # for Rt
    # rt_padded = pd.Series(np.zeros(n_days), index=cols_nccs)
    # has_rt = False
    # if max(news) > 10:
    #     # calcuate the Rt here
    #     cases = row[cols_nccs]
    #     rt = get_Rt.get_Rt(cases, cutoff=5, sigma=.25, calc_hdis=False)
    #     if rt is None:
    #         # this region doesn't meet the number of cases requirement
    #         has_rt = False
    #     else:
    #         # this region has enough data!
    #         has_rt = True
    #         # fix NAN
    #         rt['ML'] = rt['ML'].fillna(0)
    #         # round
    #         rt['ML'] = rt['ML'].round(2)
    #         # pad the days with zero
    #         rt_padded = rt_padded.add(rt["ML"], fill_value=0)
    # else:
    #     pass

    # prepare output data
    output_data[FIPS] = {
        'state': state,
        'FIPS': FIPS,
        'countyFIPS': idxFIPS,
        'lat': row['lat'],
        'lon': row['lon'],
        'countyName': countyName.replace(' County', ''),
        # 'has_rt': has_rt,
        # 'rt_ml': rt_padded.values.tolist(),
        'cdts': [ row[dt + '_cdt'] for dt in dates_w4dm[smooth_days:] ],
        'nccs': [ row[dt + '_ncc'] for dt in dates_w4dm[smooth_days:] ],
        'news': news,
        'dths': [ row[dt + '_dth'] for dt in dates_w4dm[smooth_days:] ],
        'sdrs': [ row[dt + '_sdr'] for dt in dates_w4dm[smooth_days:] ],
        'd_cdt': row[col_last1 + '_d_cdt'],
        'd_ncc': row[col_last1 + '_d_ncc'],
        'd_dth': row[col_last1 + '_d_dth'],
        'd_sdr': row[col_last1 + '_d_sdr']
    }

# want to know how many has rt?
# num_has_rt = sum([ output_data[k]['has_rt'] for k in output_data ])
# print('* %d has rt, and %d not enough data' % (num_has_rt, len(output_data.keys()) - num_has_rt))

output_json = {
    'date': col_last1,
    'dates': dates_w4dm[smooth_days:].tolist(),
    'data': output_data
}

#%% output the all history data
json.dump(output_json, open(FN_OUTPUT_COUNTY_DATA_HIS, 'w'), indent=2)
print('* saved %s days of json of CASES, CDT, DEATH, DEATH RATE data of all counties %s' % (n_days, FN_OUTPUT_COUNTY_DATA_HIS))

#%% output the latest for vis
# cols = ['rt_ml', 'cdts', 'nccs', 'news', 'dths', 'sdrs']
cols = ['cdts', 'nccs', 'news', 'dths', 'sdrs']
output_json['dates'] = output_json['dates'][-n_days_cut:]
for state in output_json['data']:
    for col in cols:
        # cut the values
        output_json['data'][state][col] = output_json['data'][state][col][-n_days_cut:]

json.dump(output_json, open(FN_OUTPUT_COUNTY_DATA, 'w'), indent=2)
print('* saved json of CASES, CDT, DEATH, DEATH RATE data of all counties %s' % FN_OUTPUT_COUNTY_DATA)


#%% Compute US State Cases Doubling Time (CDT) and Rt
# to get the correct Rt, we need to set a correct date range.
# so... we set 1/26/20 for every state
# and we will cut the last 30 days of all results for display.
print("""
###############################################################
# US State Cases Doubling Time and Rt to %s
###############################################################
""" % FN_OUTPUT_STATE_DATA)

col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]

# set the start date
n_days_cut = 30
start_date = '1/26/20'
idx_start_date = covid_data.columns.values.tolist().index(start_date)
col_lastns = covid_data.columns[idx_start_date:]
n_days = len(covid_data.columns[idx_start_date:])
col_ndays_ago = col_lastns[0]
print('* there will be %s days since %s to today' % (n_days, col_ndays_ago))
print('* the last %s days will be used for display' % (n_days_cut))

# make a copy and do everything on this copy
dft = covid_data[:]

# merge with the death data
dft = dft.merge(death_data.loc[:, death_data.columns[3:]], 
    left_index=True, right_index=True, suffixes=['_ncc', '_dth'])

# merge the data to state level
dft = dft.groupby('State').sum()
dft = dft.loc[:, dft.columns[1:]]
dft.loc['US', :] = dft.sum()

# smooth for the CDT
smooth_days = 4
dates_w4dm = covid_data.columns[-(n_days + smooth_days):]

# do the math!
print('* calculating the CDT and SDR')
for i in tqdm(range(smooth_days, len(dates_w4dm))):
    dt_today = dates_w4dm[i]
    dt_ystdy = dates_w4dm[i-1]
    dt_ndago = dates_w4dm[i-smooth_days]

    # get the cdt
    dft.loc[:, dt_today + '_cdt'] = \
        smooth_days * np.log(2) / np.log((dft[dt_today + '_ncc'] + 0.5) / dft[dt_ndago + '_ncc'])
    
    # get the new cases
    dft.loc[:, dt_today + '_new'] = \
        dft[dt_today + '_ncc'] - dft[dt_ystdy + '_ncc']

    # get the death rate
    dft.loc[:, dt_today + '_sdr'] = \
        ( dft[dt_today + '_dth'] - dft[dt_ndago + '_dth'] ) / \
        ( dft[dt_today + '_ncc'] - dft[dt_ndago + '_ncc'] + 0.5 )

    # cut values
    dft.loc[:, dt_today + '_cdt'] = dft[dt_today + '_cdt'].where( \
        ~(dft[dt_today + '_cdt']>CUT_VALUE), CUT_VALUE)

    # fix 0
    dft.loc[:, dt_today + '_cdt'] = dft[dt_today + '_cdt'].where( \
        ~(dft[dt_today + '_cdt']==0), CUT_VALUE)

    # fix death rate
    dft.loc[:, dt_today + '_sdr'] = dft[dt_today + '_sdr'].where( \
        ~(dft[dt_today + '_sdr']>0.2), 0)

# get the latest delta
dft.loc[:, col_last1 + '_d_cdt'] = dft[col_last1 + '_cdt'] - dft[col_last2 + '_cdt']
dft.loc[:, col_last1 + '_d_ncc'] = dft[col_last1 + '_ncc'] - dft[col_last2 + '_ncc']
dft.loc[:, col_last1 + '_d_dth'] = dft[col_last1 + '_dth'] - dft[col_last2 + '_dth']
dft.loc[:, col_last1 + '_d_sdr'] = dft[col_last1 + '_sdr'] - dft[col_last2 + '_sdr']

# fix death rate Nan
dft.loc[:, col_last1 + '_d_sdr'] = dft.loc[:, col_last1 + '_d_sdr'].fillna(0)

# calculate the Rt and prepare the all history data
cols_nccs = [ '%s_ncc'%v for v in dates_w4dm[smooth_days:].tolist() ]
output_data = {}
# print('* calculating the Rt')
for state, row in tqdm(dft.iterrows()):
    # calcuate the Rt here
    # cases = row[cols_nccs]
    # rt = get_Rt.get_Rt(cases, cutoff=10, sigma=.25, calc_hdis=False)    
    # rt_padded = pd.Series(np.zeros(n_days), index=cols_nccs)
    # has_rt = True
    
    # if rt is None:
    #     # this region doesn't meet the number of cases requirement
    #     has_rt = False
    # else:
    #     # fix NAN
    #     rt['ML'] = rt['ML'].fillna(0)
    #     # pad the days with zero
    #     rt_padded = rt_padded.add(rt["ML"], fill_value=0)

    # make the output data
    output_data[state] = {
        'state': state,
        # 'rt_ml': rt_padded.values.tolist(),
        # 'has_rt': has_rt,
        'cdts': [ row[dt + '_cdt'] for dt in dates_w4dm[smooth_days:] ],
        'nccs': [ row[dt + '_ncc'] for dt in dates_w4dm[smooth_days:] ],
        'news': [ row[dt + '_new'] for dt in dates_w4dm[smooth_days:] ],
        'dths': [ row[dt + '_dth'] for dt in dates_w4dm[smooth_days:] ],
        'sdrs': [ row[dt + '_sdr'] for dt in dates_w4dm[smooth_days:] ],
        'd_cdt': row[col_last1 + '_d_cdt'],
        'd_ncc': row[col_last1 + '_d_ncc'],
        'd_dth': row[col_last1 + '_d_dth'],
        'd_sdr': row[col_last1 + '_d_sdr']
    }

# want to know how many has rt?
# num_has_rt = sum([ output_data[k]['has_rt'] for k in output_data ])
# print('* %04d has rt, and %04d not' % (num_has_rt, len(output_data.keys()) - num_has_rt))

#%% output the all history data
output_json = {
    'date': col_last1,
    'dates': dates_w4dm[smooth_days:].tolist(),
    'data': output_data
}
json.dump(output_json, open(FN_OUTPUT_STATE_DATA_HIS, 'w'), indent=2)
print('* saved %d days output_json of CASES, CDT, DEATH, DEATH RATE data of all states %s' % (n_days, FN_OUTPUT_STATE_DATA_HIS))

#%% output the latest N days data for visualization
# cols = ['rt_ml', 'cdts', 'nccs', 'news', 'dths', 'sdrs']
cols = ['cdts', 'nccs', 'news', 'dths', 'sdrs']
output_json['dates'] = output_json['dates'][-n_days_cut:]
for state in output_json['data']:
    for col in cols:
        # cut the values
        output_json['data'][state][col] = output_json['data'][state][col][-n_days_cut:]
json.dump(output_json, open(FN_OUTPUT_STATE_DATA, 'w'), indent=2)
print('* saved %d days cutted output_json of CASES, CDT, DEATH, DEATH RATE data of all states %s' % (n_days_cut, FN_OUTPUT_STATE_DATA))



#%% Update last_update time
print("""
###############################################################
# SYSTEM Last Update: %s
###############################################################
""" % FN_LAST_UPDATE)
last_update = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
json.dump({
    'last_update': last_update
}, open(FN_LAST_UPDATE, 'w'))

print('* updated last_updated: %s' % last_update)

