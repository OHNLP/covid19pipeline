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

import dateparser

from tqdm import tqdm

import matplotlib.pyplot as plt

print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst/dsvm')

FN_OUTPUT_STATE_TEST = os.path.join(FOLDER_RST, 'usstate-test-latest.json')
FN_OUTPUT_STATE_TEST_DICT = os.path.join(FOLDER_RST, 'usstate-data-dict-latest.json')
FN_OUTPUT_STATE_DATA = os.path.join(FOLDER_RST, 'usstate-data-latest.json')

CUT_VALUE = 100

# last time update
FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')
print('* defined the filenames:')
for v in dir():
    if v.startswith('FN_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

# define data sources
DS_COVIDTRACKING_STATEDAILY = 'https://covidtracking.com/api/v1/states/daily.csv'

print('* defined the data sourcess:')
for v in dir():
    if v.startswith('DS_'):
        print('*   %s: %s' % (v, eval(v)))
print('')


#%% State Level Data
print("""
###############################################################
# Get State Latest from Covid-19 tracking
###############################################################
""")

df = pd.read_csv(DS_COVIDTRACKING_STATEDAILY)
df.sort_values(by=['state', 'date'], inplace=True)
df.reset_index(inplace=True)
df.drop(columns=['index'], inplace=True)
print('* loaded data from %s' % DS_COVIDTRACKING_STATEDAILY)


#%% parse the data
dft = df[:]
smooth_day = 4
today = dft['date'].values[-1]
# n_days = 30
# n_days_ago = dft['date'].values[-n_days - 1]
n_days_ago = 20200320
dates = [ x for x in pd.date_range('%s' % n_days_ago, '%s' % today) ]
states = dft['state'].unique()

for state in tqdm(states):
    for i, date in enumerate(dates):
        if i<smooth_day: continue
        dt_v = int(date.strftime('%Y%m%d'))
        dt_v2 = int(dates[i-smooth_day].strftime('%Y%m%d'))
        n_pos_today = dft[(dft['date']==dt_v) & (dft['state']==state)]['positive'].values[0]
        n_pos_ndago = dft[(dft['date']==dt_v2) & (dft['state']==state)]['positive'].values[0]
        n_tot_today = dft[(dft['date']==dt_v) & (dft['state']==state)]['total'].values[0]
        n_tot_ndago = dft[(dft['date']==dt_v2) & (dft['state']==state)]['total'].values[0]

        # test positive rate
        tpr_ndm = (n_pos_today - n_pos_ndago) / (n_tot_today - n_tot_ndago)
        dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'tpr_ndm'] = tpr_ndm

        # CDT
        cdt = smooth_day * np.log(2) / np.log( (n_pos_today+0.5) / n_pos_ndago )
        dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'cdt'] = cdt

# fill the NaN values
dft['positive'].fillna(0, inplace=True)
# total number didn't change will cause Infinite value
dft['tpr_ndm'].replace([np.inf], None, inplace=True)
# Nan value in positive
dft['tpr_ndm'].fillna(0, inplace=True)
# too large
dft['tpr_ndm'].where(~(dft['tpr_ndm']>0.75), None, inplace=True)
# too small
dft['tpr_ndm'].where(~(dft['tpr_ndm']<0), None, inplace=True)
# Nan value in death
dft['death'].fillna(0, inplace=True)
# Nan value in cdt
dft['cdt'].fillna(CUT_VALUE, inplace=True)
# too large cdt
dft['cdt'].where(~(dft['cdt']>CUT_VALUE), CUT_VALUE, inplace=True)

print('\n* calculated the %s day smoothed test positive rate' % smooth_day)


#%% output the data to dictionary format for front-end use
output_data = {}
for state in tqdm(states):
    output_data[state] = {}
    for i, date in enumerate(dates):
        dt_v = int(date.strftime('%Y%m%d'))
        dt_str = date.strftime('%-m/%-d/%Y')
        tpr = dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'tpr_ndm'].values[0]
        if np.isnan(tpr):
            tpr = None
        output_data[state][dt_str] = {
            'cdt': float(dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'cdt'].values[0]),
            'dth': int(dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'death'].values[0]),
            'test_tot': int(dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'total'].values[0]),
            'test_pos': int(dft.loc[(dft['date']==dt_v) & (dft['state']==state), 'positive'].values[0]),
            'test_tpr_4dm': tpr
        }

print('* get state level data')
output_json = {
    'date': dates[-1].strftime('%-m/%-d/%Y'),
    'dates': [ dt.strftime('%-m/%-d/%Y') for dt in dates ],
    'data': output_data
}
json.dump(output_json, open(FN_OUTPUT_STATE_TEST_DICT, 'w'))
print('* outputed to %s' % FN_OUTPUT_STATE_TEST_DICT)


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