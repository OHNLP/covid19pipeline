#%% load packages
import os
import random
import math
import json
import time
import datetime
import dateutil
import pathlib

from functools import reduce

import numpy as np
import pandas as pd

# import get_Rt

from tqdm import tqdm

print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst/dsvm')

FN_COUNTY = os.path.join(FOLDER_RAW, 'county_stat_data.csv')
FN_OUTPUT = os.path.join(FOLDER_RST, 'uscounty-cdt-latest.json')
FN_OUTPUT_US_CASES = os.path.join(FOLDER_RST, 'uscounty-cases-latest.json')

# mayo regions
FN_OUTPUT2 = os.path.join(FOLDER_RST, 'mayo-cdt-latest.json')
FN_OUTPUT_CDTS = os.path.join(FOLDER_RST, 'mayo_regions_cdts.json')
FN_OUTPUT_MORT = os.path.join(FOLDER_RST, 'mayo_regions_mort.json')
FN_OUTPUT_NCCS = os.path.join(FOLDER_RST, 'mayo_regions_cases.json')
FN_OUTPUT_NEW_CUM_CASES = os.path.join(FOLDER_RST, 'mayo_regions_new_cum_cases.json')
FN_OUTPUT_DATA = os.path.join(FOLDER_RST, 'mayo-data-latest.json')

# mayo prediction
FN_OUTPUT_PRED = os.path.join(FOLDER_RST, 'mayo-cdt-prediction.json')
FN_LAST_UPDATE = os.path.join(FOLDER_RST, 'last_update.json')

CUT_VALUE = 100

print('* defined variables!')


#%% Load county level data
print("""
###############################################################
# Get US County Data from usafactsstatic.blob.core.windows.net
###############################################################
""")
county_data = pd.read_csv(FN_COUNTY)
covid_data = pd.read_csv('https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv')
# covid_data = pd.read_csv(os.path.join(FOLDER_RAW, 'covid_data_usafacts_04152020.csv'))
death_data = pd.read_csv('https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv')
# death_data['4/15/20'] = death_data['4/14/20']
# apply patch on MN:Hennepin County:27053

covid_data.set_index('countyFIPS', inplace=True)
county_data.set_index('countyFIPS', inplace=True)
death_data.set_index('countyFIPS', inplace=True)

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
]
for patch in patches:
    for corr in patch[1]:
        covid_data.loc[patch[0], corr[0]] = corr[1]
    print('* add patch on %s' % patch[0])


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

# rename column!!!
# how can they change header date format!!!
cols_need_rename = {}
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

cols_need_rename = {}
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

# covid_data = county_data.merge(covid_data, left_index=True, right_index=True)
covid_data = covid_data[covid_data.index > 0]

print('* loaded data! %s covid, %s death' % (len(covid_data), len(death_data)))


col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]
if col_last1 not in death_data.columns:
    death_data[col_last1] = death_data[col_last2]
    print('! %s NOT exists in death data, use %s instead!' % (col_last1, col_last2))
else:
    print('* great, death data is aligned with covid data!')
time.sleep(.888)

#%% Define the regions used in the following data generation
###############################################################
# Mayo 6 Regions
###############################################################
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
# AVG as the total or average
mc_region_list.append({
    'name': 'AVG',
    'fips': reduce(lambda x,y: x + y, [ r['fips'] for r in mc_region_list ])
})
print("* defined 6 Mayo regions")



#%% the Rt
print("""
###############################################################
# Mayo 6 Regions Rt and data latest %s
###############################################################
""" % FN_OUTPUT_DATA)
start_date = '1/26/20'
idx_start_date = covid_data.columns.values.tolist().index(start_date)
n_days = len(covid_data.columns[idx_start_date:])
col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]
tmp = []
for hrr in mc_region_list:
    hrr_sum = covid_data.loc[covid_data.index.isin(hrr['fips']), covid_data.columns[3:]].sum()
    hrr_df = pd.DataFrame(hrr_sum, columns=[hrr['name']]).T
    tmp.append(hrr_df)

mayo_data = pd.concat(tmp)
dft = mayo_data[:]

cols_nccs = dft.columns[-n_days:]
output_data = {}
for idxHRR, row in tqdm(dft.iterrows()):
    # calcuate the Rt here
    # cases = row[cols_nccs]
    # rt = get_Rt.get_Rt(cases, cutoff=5, sigma=.25, calc_hdis=False)
    # # fix NAN
    # rt['ML'] = rt['ML'].fillna(0)
    # # pad the days with zero
    # rt_padded = pd.Series(np.zeros(n_days), index=cols_nccs)
    # rt_padded = rt_padded.add(rt["ML"], fill_value=0)

    output_data[idxHRR] = {
        # "val": rt_padded[-1],
        # "delta": rt_padded[-1] - rt_padded[-2],
        # "rt_ml": rt_padded.values.tolist()
    }

#%% output the Rt
output_json = {
    "name": 'Case Reproduction Time',
    "last_updated": col_last1,
    "regions": [ r['name'] for r in mc_region_list ],
    "dates": cols_nccs.tolist(),
    "values": output_data
}

json.dump(output_json, open(FN_OUTPUT_DATA, 'w'), indent=2)
print('* saved json of mayo reproduction time data %s' % FN_OUTPUT_DATA)



#%% the CDT 
print("""
###############################################################
# Mayo 6 Regions CDT Latest %s
###############################################################
""" % FN_OUTPUT2)
n_days = 30
col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]

mayo_data = pd.DataFrame(columns = covid_data.columns[3:],
                        index = [ r['name'] for r in mc_region_list])
# cdt need 4 days, so will have 4 days padding                   
mayo_cdts = pd.DataFrame(columns = mayo_data.columns[4:],
                        index = [ r['name'] for r in mc_region_list])

threshold_3 = 10 # or 10
for region in mc_region_list:
    reg_name = region['name']
    reg_fips = region['fips']

    # count the number of regions by sum column, fill in mayo_data
    mayo_region_series = covid_data.loc[covid_data.index.isin(reg_fips), covid_data.columns[3:]].sum()
    mayo_data.loc[reg_name, :] = mayo_region_series

    # count the doubling?
    mytmppred = []
    for day in range (mayo_cdts.columns.__len__()):
        mytmp = CUT_VALUE
        if(mayo_region_series[day] > threshold_3):
            mytmp = 4 * (np.log(2) / np.log((mayo_region_series[4+day] + 0.5) /mayo_region_series[day]))
        mytmppred.append(mytmp)
    mayo_cdts.loc[reg_name, :] = mytmppred
    mayo_cdts[mayo_cdts > CUT_VALUE] = CUT_VALUE

mayo_pred = mayo_cdts.loc[:, mayo_cdts.columns[-n_days:]].merge(
    mayo_data.loc[mayo_cdts.index,
    mayo_data.columns[-n_days:]],
    left_index=True, right_index=True, suffixes=['_cdt', '_ncc']
)

mayo_pred['delta'] = mayo_pred[col_last1+'_cdt'] - mayo_pred[col_last2+'_cdt']

j = json.loads(mayo_pred.to_json(orient='table'))
data = {
    'date': col_last1,
    'data': j['data']
}
json.dump(data, open(FN_OUTPUT2, 'w'), indent=2)
print('* saved json of mayo counties data %s' % FN_OUTPUT2)


#%% the cases 
print("""
###############################################################
# Mayo 6 Regions Cases and New Cases %s
###############################################################
""" % FN_OUTPUT2)
col_last1 = covid_data.columns[-1]
col_last30s = covid_data.columns[-30:]

# mayo_data is already got at previous step
mayo6_newcase_df = mayo_data.loc[:, []]
for i in range(len(mayo_data.columns)-1, len(mayo_data.columns)-1-30, -1):
    col = mayo_data.columns[i]
    col_prev = mayo_data.columns[i-1]
    mayo6_newcase_df[col] = mayo_data[col] - mayo_data[col_prev]

data = {
    'date': col_last1,
    'dates': col_last30s.tolist(),
    'data': {}
}

for region in mc_region_list:
    reg_name = region['name']
    data['data'][reg_name] = {
        'cum_cases': mayo_data.loc[reg_name, col_last30s].tolist(),
        'new_cases': mayo6_newcase_df.loc[reg_name, col_last30s].tolist()
    }

json.dump(data, open(FN_OUTPUT_NEW_CUM_CASES, 'w'), indent=2)
print('* saved json of mayo new and cum cases data %s' % FN_OUTPUT_NEW_CUM_CASES)


#%% the total positive test
print("""
###############################################################
# Mayo 6 Regions Total Positive Tests N days %s
###############################################################
""" % FN_OUTPUT_NCCS)
n_days = 30
col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]
col_lastns = covid_data.columns[-n_days:]

regions = [ r['name'] for r in mc_region_list ]
regions.remove('AVG')

mayo_pred['ncc_delta'] = mayo_pred[col_last1+'_ncc'] - mayo_pred[col_last2+'_ncc']

values = {}
for reg in mc_region_list:
    reg_name = reg['name']

    value = {
        "val": int(mayo_pred.loc[reg_name, col_last1 + '_ncc']),
        "delta": int(mayo_pred.loc[reg_name, 'ncc_delta']),
        "history": list(map(int, mayo_pred.loc[reg_name, [ dt + '_ncc' for dt in col_lastns.tolist()]].tolist()))
    }
    if reg_name == 'AVG': reg_name = 'TOTAL'
    values[reg_name] = value

data = {
    'name': 'Total Positive Tests',
    "last_updated": col_last1,
    "regions": regions,
    "dates": col_lastns.tolist(),
    "values": values
}
json.dump(data, open(FN_OUTPUT_NCCS, 'w'), indent=2)
print('* saved json of mayo regions data %s' % FN_OUTPUT_NCCS)


#%% the mortality rate
print("""
###############################################################
# Mayo 6 Regions Cases Doubling Time N days %s
###############################################################
""" % FN_OUTPUT_CDTS)
n_days = 30
col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]
col_lastns = covid_data.columns[-n_days:]

regions = [ r['name'] for r in mc_region_list ]
regions.remove('AVG')

values = {}
for reg in mc_region_list:
    value = {
        "val": mayo_pred.loc[reg['name'], col_last1 + '_cdt'],
        "delta": mayo_pred.loc[reg['name'], 'delta'],
        "history": mayo_pred.loc[reg['name'], [ dt + '_cdt' for dt in col_lastns.tolist()]].tolist()
    }
    values[reg['name']] = value
data = {
    'name': 'Cases Doubling Time',
    "last_updated": col_last1,
    "regions": regions,
    "dates": col_lastns.tolist(),
    "values": values
}
json.dump(data, open(FN_OUTPUT_CDTS, 'w'), indent=2)
print('* saved json of mayo regions data %s' % FN_OUTPUT_CDTS)


#%% the mortality rate
print("""
###############################################################
# Mayo 6 Regions Mortality Rate 7 days %s
###############################################################
""" % FN_OUTPUT_MORT)
n_days = 30
col_last1 = covid_data.columns[-1]
col_last2 = covid_data.columns[-2]
col_lastns = covid_data.columns[-n_days:]

combined2 = covid_data.merge(
    death_data,
    left_index=True, right_index=True,
    suffixes=['_ncc', '_dth']
)

mayo_mort_data = pd.DataFrame(
    columns = [ dt + '_ncc' for dt in col_lastns.tolist() ] +
        [ dt + '_dth' for dt in col_lastns.tolist() ],
    index = [ r['name'] for r in mc_region_list ]
)

for region in mc_region_list:
    reg_name = region['name']
    reg_fips = region['fips']

    mayo_mort_data_reg = combined2.loc[
        combined2.index.isin(reg_fips),
        [ dt + '_ncc' for dt in col_lastns ] + [ dt + '_dth' for dt in col_lastns ]
    ].sum()
    mayo_mort_data.loc[reg_name, :] = mayo_mort_data_reg

    for col in col_lastns.tolist():
        n_cases = mayo_mort_data.loc[reg_name, col + '_ncc']
        if n_cases > 0:
            mayo_mort_data.loc[reg_name, col + '_mort'] = mayo_mort_data.loc[reg_name, col + '_dth'] / n_cases
        else:
            mayo_mort_data.loc[reg_name, col + '_mort'] = np.nan

mayo_mort_data['delta'] = mayo_mort_data[col_last1+'_mort'] - mayo_mort_data[col_last2+'_mort']

regions = [ r['name'] for r in mc_region_list ]
regions.remove('AVG')

values = {}
for reg in mc_region_list:
    value = {
        "val": mayo_mort_data.loc[reg['name'], col_last1 + '_mort'],
        "delta": mayo_mort_data.loc[reg['name'], 'delta'],
        "history": mayo_mort_data.loc[reg['name'], [ dt + '_mort' for dt in col_lastns.tolist()]].tolist()
    }
    values[reg['name']] = value
data = {
    'name': 'Mortality Rate',
    "last_updated": col_last1,
    "regions": regions,
    "dates": col_lastns.tolist(),
    "values": values
}
json.dump(data, open(FN_OUTPUT_MORT, 'w'), indent=2)
print('* saved json of mayo regions mortallity data %s' % FN_OUTPUT_MORT)


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
