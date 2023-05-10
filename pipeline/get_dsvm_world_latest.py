#%% load packages
import os
import random
import math
import json
import datetime
import dateutil
import pathlib
import argparse

import numpy as np
import pandas as pd

from tqdm import tqdm

# import get_Rt

print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst/dsvm')
FN_OUTPUT_WORLD = os.path.join(FOLDER_RST, 'world-cdt-latest.json')
FN_OUTPUT_WORLD_LATEST = os.path.join(FOLDER_RST, 'world-data-latest.json')
FN_OUTPUT_WORLD_HISTORY = os.path.join(FOLDER_RST, 'world-data-history.json')

CUT_VALUE = 100

# last time update
FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')
print('* defined the filenames:')
for v in dir():
    if v.startswith('FN_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

# define data sources
DS_CSSE_WORLD_CONFIRMED = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
DS_CSSE_WORLD_DEATH = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
DS_CSSE_WORLD_RECOVER = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'


print('* defined the data sourcess:')
for v in dir():
    if v.startswith('DS_'):
        print('*   %s: %s' % (v, eval(v)))
print('')


#%% World Level Data
print("""
###############################################################
# Get World All Data from %s
###############################################################
""" % DS_CSSE_WORLD_CONFIRMED)

confirmed_df = pd.read_csv(DS_CSSE_WORLD_CONFIRMED)
deaths_df = pd.read_csv(DS_CSSE_WORLD_DEATH)
recoveries_df = pd.read_csv(DS_CSSE_WORLD_RECOVER)
print('* loaded data %s lines' % len(confirmed_df))

# need to combine the data to country level
confirmed_df = confirmed_df.groupby(['Country/Region']).sum()
deaths_df = deaths_df.groupby(['Country/Region']).sum()
confirmed_df.reset_index(inplace=True)
deaths_df.reset_index(inplace=True)
print('* compressed into %s lines' % len(confirmed_df))


#%% get world history
print("""
###############################################################
# Get World Data History since 1/26/2020
###############################################################
""")
col_last1 = confirmed_df.columns[-1]
col_last2 = confirmed_df.columns[-2]
ids = 0
for i, col in enumerate(confirmed_df.columns):
    if col == '1/26/20':
        ids = i
        break
col_lastns = confirmed_df.columns[ids:]
n_cols = len(confirmed_df.columns)
n_days = len(col_lastns)
col_ndays_ago = col_lastns[0]
print('* there will be %s days since %s to today' % (n_days, col_ndays_ago))

# copy dataframe for following 
dft1 = confirmed_df[:]
dft2 = deaths_df[:]

dft1.set_index('Country/Region', inplace=True)
dft2.set_index('Country/Region', inplace=True)
dft1.loc['WORLD', :] = dft1.sum()
dft2.loc['WORLD', :] = dft2.sum()

countries = dft1.index.tolist()
smooth_days = 4
output_json = {
    'date': col_last1,
    'dates': [],
    'data': dict([ (c, {
        'country': c, 
        'cdts': [], 
        'nccs': [], 
        'news': [], 
        'dths': [], 
        'ndes': [],
        'sdrs': []
    }) for c in countries ])
}

dates_with4 = dft1.columns[(ids-4):]
print('* calculating the CDT and SDR')
for i in tqdm(range(4, len(dates_with4))):
    today = dates_with4[i]
    ystdy = dates_with4[i-1]
    ndago = dates_with4[i-4]

    # calculate new, cdt and sdr
    dft1[today + '_new'] = dft1[today] - dft1[ystdy]
    dft1[today + '_cdt'] = smooth_days * ( np.log(2) / np.log( (dft1[today] + 0.5) / (dft1[ndago]) ) )
    dft1[today + '_cdt'].where(~(dft1[today + '_cdt']<=0), CUT_VALUE, inplace=True)
    dft1[today + '_cdt'].where(~(dft1[today + '_cdt']>CUT_VALUE), CUT_VALUE, inplace=True)
    
    dft1[today + '_sdr'] = ( dft2[today] - dft2[ndago] ) / (dft1[today] - dft1[ndago] + 0.5)
    dft1[today + '_sdr'].fillna(0, inplace=True)
    dft1[today + '_sdr'].where(~(dft1[today + '_sdr']>0.15), 0.15, inplace=True)

    dft2[today + '_nde'] = dft2[today] - dft2[ystdy]

    # put value in output
    output_json['date'] = today
    output_json['dates'].append(today)
    for c in countries:
        output_json['data'][c]['nccs'].append(int(dft1.loc[c, today]))
        output_json['data'][c]['dths'].append(int(dft2.loc[c, today]))
        output_json['data'][c]['ndes'].append(int(dft2.loc[c, today + '_nde']))
        output_json['data'][c]['news'].append(int(dft1.loc[c, today + '_new']))
        output_json['data'][c]['cdts'].append(dft1.loc[c, today + '_cdt'])
        output_json['data'][c]['sdrs'].append(dft1.loc[c, today + '_sdr'])

# print('* calculating the Rt')
# add the rt
# for c in tqdm(countries):
#     # calcuate the Rt here
#     rt_cases = pd.Series(output_json['data'][c]['nccs'], index=output_json['dates'])
#     rt = get_Rt.get_Rt(rt_cases, cutoff=25, sigma=.25, calc_hdis=False)
#     rt_padded = pd.Series(np.zeros(n_days), index=col_lastns)
#     has_rt = True

#     if rt is None:
#         has_rt = False
#     else:
#         # fix NAN
#         rt['ML'] = rt['ML'].fillna(0)
#         # pad the days with zero
#         rt_padded = rt_padded.add(rt["ML"], fill_value=0)

#     # bind data
#     output_json['data'][c]['has_rt'] = has_rt
#     output_json['data'][c]['rt_ml'] = rt_padded.values.tolist()

# num_has_rt = sum([ output_json['data'][k]['has_rt'] for k in output_json['data'] ])
# print('* %04d has rt, and %04d NOT' % (num_has_rt, len(output_json['data'].keys()) - num_has_rt))

json.dump(output_json, open(FN_OUTPUT_WORLD_HISTORY, 'w'), indent=2)
print('* created global data %s history' % FN_OUTPUT_WORLD_HISTORY)



#%% get world latest
print("""
###############################################################
# Get World Data Latest since 1/26/2020
###############################################################
""")
# in fact, the history and latest are same, the difference is format.
# we can use the history data to produce
start_num_cases = 400
out2 = {
    'date': output_json['date'],
    'data': {}
}
for c in output_json['data']:
    s = pd.Series(output_json['data'][c]['nccs'], index=output_json['dates'])
    idx_dates = s[s>start_num_cases].index
    if len(idx_dates) == 0: continue

    # ok, this country has enough data
    idx = output_json['dates'].index(idx_dates[0])
    out2['data'][c] = {}

    # put values
    out2['data'][c]['dates'] = output_json['dates'][idx:]
    out2['data'][c]['nccs'] = output_json['data'][c]['nccs'][idx:]
    out2['data'][c]['cdts'] = output_json['data'][c]['cdts'][idx:]
    out2['data'][c]['dths'] = output_json['data'][c]['dths'][idx:]
    out2['data'][c]['ndes'] = output_json['data'][c]['ndes'][idx:]
    out2['data'][c]['news'] = output_json['data'][c]['news'][idx:]
    out2['data'][c]['nccs'] = output_json['data'][c]['nccs'][idx:]
    out2['data'][c]['sdrs'] = output_json['data'][c]['sdrs'][idx:]
    # out2['data'][c]['rt_ml'] = output_json['data'][c]['rt_ml'][idx:]
    # out2['data'][c]['has_rt'] = output_json['data'][c]['has_rt']

print('\n* get all the latest of %d/%d countries' % (len(out2['data']), len(countries)))
json.dump(out2, open(FN_OUTPUT_WORLD_LATEST, 'w'), indent=2)
print('* created global data %s' % FN_OUTPUT_WORLD_LATEST)
        
#%% get old style world CDT
# print("""
# ###############################################################
# # Get World CDT from raw.githubusercontent.com/CSSEGISandData
# ###############################################################
# """)
# #%% parse to map data
# col_last1 = confirmed_df.columns[-1]
# col_last2 = confirmed_df.columns[-2]
# col_last3s = confirmed_df.columns[-3:]

# globalpredictionSeries = confirmed_df.loc[confirmed_df[confirmed_df.columns[-1]] > 400, confirmed_df.columns[8:confirmed_df.columns.__len__()]].copy()
# for day in range (globalpredictionSeries.columns.__len__()):
#     mytmppred=[]
#     for ind in globalpredictionSeries.index:
#         mytmp = np.nan
#         if(confirmed_df.loc[ind, confirmed_df.columns[4+day]] > 10):
#             mytmp = 4 * (np.log(2) / np.log((confirmed_df.loc[ind,confirmed_df.columns[8+day]] + 0.5) /confirmed_df.loc[ind, confirmed_df.columns[4+day]] ))
#             if mytmp < 0:
#                 mytmp = CUT_VALUE
#         mytmppred.append(mytmp)
#     globalpredictionSeries[globalpredictionSeries.columns[day]]=mytmppred
# globalpredictionSeries[globalpredictionSeries > CUT_VALUE] = CUT_VALUE

# x = confirmed_df.loc[globalpredictionSeries.index,confirmed_df.columns[0:2]]
# globalseries=globalpredictionSeries.merge(x, left_index=True, right_index=True)
# globaldata = globalseries.merge(
#     confirmed_df.loc[globalseries.index, confirmed_df.columns[confirmed_df.columns.__len__()-7:confirmed_df.columns.__len__()]],
#     left_index=True, right_index=True
# )

# # globaldata.to_csv('./static/data/cdt/GlobalDoublingTimeResult_4Days.csv')

# # rename the outdata
# outdata = globaldata[
#     ['Country/Region'] + [ col + '_x' for col in col_last3s ]
# ]
# cols_need_rename = dict([ (col + '_x', col+'_cdt') for col in col_last3s ])
# cols_need_rename['Country/Region'] = 'country'
# outdata.rename(columns=cols_need_rename, inplace=True)

# # merge the case data
# wd_case_7days = confirmed_df.loc[:, confirmed_df.columns[-7:]]
# cols_need_rename = dict([ (col, col+'_ncc') for col in col_last3s ])
# wd_case_7days.rename(columns=cols_need_rename, inplace=True)
# outdata = outdata.merge(
#     wd_case_7days.loc[outdata.index, :], 
#     left_index=True, right_index=True)

# # merge the death data
# wd_death_7days = deaths_df.loc[:, deaths_df.columns[-7:]]
# cols_need_rename = dict([ (col, col+'_dth') for col in col_last3s ])
# wd_death_7days.rename(columns=cols_need_rename, inplace=True)
# outdata = outdata.merge(
#     wd_death_7days.loc[outdata.index, :], 
#     left_index=True, right_index=True)

# # calc the delta
# outdata['delta_cdt'] = outdata[col_last1+'_cdt'] - outdata[col_last2+'_cdt']
# outdata['delta_ncc'] = outdata[col_last1+'_ncc'] - outdata[col_last2+'_ncc']
# outdata['delta_dth'] = outdata[col_last1+'_dth'] - outdata[col_last2+'_dth']

# # output
# j = json.loads(outdata.to_json(orient='table'))
# world_data = {
#     'date': col_last1,
#     'data': j['data']
# }
# json.dump(world_data, open(FN_OUTPUT_WORLD, 'w'), indent=2)
# print('* created global doubling time 4days %s' % FN_OUTPUT_WORLD)


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