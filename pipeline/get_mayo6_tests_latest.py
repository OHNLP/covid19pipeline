#%% load packages
import os
import json
import pathlib
import datetime

import pandas as pd

print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst')

FN_RAW_MAYO_TESTS = os.path.join(FOLDER_RAW, 'mayo_test_dashboard.csv')
FN_OUTPUT_MAYO_TESTS = os.path.join(FOLDER_RST, 'mayo_regions_tests.json')

FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')
print('* defined the filenames:')
for v in dir():
    if v.startswith('FN_'):
        print('*   %s: %s' % (v, eval(v)))
print('')

print('* defined variables')

# %% load data and merge!
mayo_sites = ['PHX', 'JAX', 'RST', 'NWWI', 'SWMN', 'SWWI']
df = pd.read_csv(FN_RAW_MAYO_TESTS)

print('* loaded mayo site data %s lines' % len(df))
print('* last line is: %s' % df.loc[df.index[-1]]['date'])

# %% test
df['RST_total_completed_tests'] = df['RST_total_completed_tests'] + df['SEMN_total_completed_tests']
df['RST_total_positive_tests'] = df['RST_total_positive_tests'] + df['SEMN_total_positive_tests']
# df['RST_total_individuals_tested_positive'] = df['RST_total_individuals_tested_positive'] + df['SEMN_total_individuals_tested_positive']
print('* merged RST and SEMN!') # then we don't need to use SEMN in the following codes

df['TOTAL_total_completed_tests'] = df[[ '%s_total_completed_tests' % s for s in mayo_sites ]].sum(axis=1)
df['TOTAL_total_positive_tests'] = df[[ '%s_total_positive_tests' % s for s in mayo_sites ]].sum(axis=1)
# df['TOTAL_total_individuals_tested_positive'] = df[[ '%s_total_individuals_tested_positive' % s for s in mayo_sites ]].sum(axis=1)
print('* merged and added the TOTAL')


#%% get smoothed 4 day test positive rate
mayo_sites = ['PHX', 'JAX', 'RST', 'NWWI', 'SWMN', 'SWWI', 'TOTAL']
dates = df['date'].tolist()
output_dates = []

for i, date in enumerate(dates):
    if i < 4: continue
    output_dates.append(date)

    for site in mayo_sites:
        t0_tot_tests = df.loc[i, site + '_total_completed_tests']
        t4_tot_tests = df.loc[i-4, site + '_total_completed_tests']
        t0_pos_tests = df.loc[i, site + '_total_positive_tests']
        t4_pos_tests = df.loc[i-4, site + '_total_positive_tests']
        
        site_4dmtpr = (t0_pos_tests - t4_pos_tests) / (t0_tot_tests - t4_tot_tests)

        df.loc[i, site + '_tpr_4dm'] = site_4dmtpr

print('* calculated the 4dmtpr for each site')

# %% convert format
data = {}
for mayo_site in mayo_sites:
    data[mayo_site] = {
        'total_completed_tests': df[df['date'].isin(output_dates)]['%s_total_completed_tests' % mayo_site].tolist(),
        'total_positive_tests': df[df['date'].isin(output_dates)]['%s_total_positive_tests' % mayo_site].tolist(),
        'tpr_4dm': df[df['date'].isin(output_dates)]['%s_tpr_4dm' % mayo_site].tolist(),
    }
print('* converted data into json format!')

# %% save results
date = df.loc[df.index[-1], 'date']

output_json = {
    'last_update': date,
    'dates': output_dates,
    'data': data
}
json.dump(output_json, open(FN_OUTPUT_MAYO_TESTS, 'w'), indent=2)
print('* dumped the converted data!')


#%% update last_update
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