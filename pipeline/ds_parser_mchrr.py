#%% load packages
import os
import sys
import math
import json
import copy
import pathlib
import datetime
import argparse
import multiprocessing
import multiprocessing.pool as mpp

from functools import reduce

from tqdm import tqdm

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

import ds_config as cfg

import ds_util
from ds_util import NpEncoder
from ds_util import _floor
from ds_util import _round

def parse_mchrr_with_actnow_and_cdcpvi_data_v2(parse_date=None):
    '''
    Parse MCHRR data for given parse_date with Actnow + CDCPVI data

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - dths: deaths
        - dtrs: death rate
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index?
        - dates: dates of the data

    And the characteristics
        - state
        - FIPS
        - pop
        - name
        - date
    '''

    # get the date if it's None
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)
        print('* got parse_date=%s from input' % parse_date)

    print("""
    ###############################################################
    # Parse ACTNOW+CDCPVI data %s to generate MCHRR-level results
    ###############################################################
    """ % (parse_date))
    
    # create the dates for parsing
    date_vals = []
    
    # get all dates
    dates = pd.date_range(cfg.FIRST_DATE, parse_date)
    for i in range(len(dates)):
        day = dates[i]
        date_vals.append(day.strftime('%Y-%m-%d'))
    print('* created dates %s to %s' % (date_vals[0], date_vals[-1]))

    # add MCHRR label
    mc_region_list = copy.copy(cfg.MC_REGIONS)
    mchrrs = [ _['name'] for _ in mc_region_list ]
    
    # get the covid data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)

    # get the actnow data
    fn_actnow_data = cfg.FN_SAVE_ACTNOW_COUNTY_DATA % parse_date
    df_actnow = pd.read_csv(fn_actnow_data)

    # set index
    # df_cdcpvi.set_index(['date', 'countyFIPS'], inplace=True)
    # print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # df_actnow.set_index(['date', 'fips'], inplace=True)
    # print('* loaded %s lines data frame from %s' % (len(df_actnow), fn_actnow_data))

    # get population data
    df_pop = pd.read_csv(cfg.FN_COUNTY_POPU)
    print('* loaded population data from %s' % cfg.FN_COUNTY_POPU)

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        pass
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))


    for _ in tqdm(mc_region_list):
        mchrr = _['name']
        fipss = _['fips']

        # get basic characteristics
        FIPS = mchrr
        state = mchrr
        name = mchrr

        pop = df_pop[df_pop['FIPS'].isin(fipss)]['POP'].sum()

        # get other values
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        dths = []
        dtrs = []
        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []

        dates = []

        # first, check the actnow data and fix the missing values
        df_actnow_mchrr = []
        for fips in fipss:
            df_actnow_mchrr_cnty = df_actnow[df_actnow['fips'] == fips].copy()
            missing_dates = []
            existing_dates = set(df_actnow_mchrr_cnty.date.values)
            for date in date_vals:
                if date not in existing_dates:
                    # missing data is very common in actnow ...
                    df_actnow_mchrr_cnty = df_actnow_mchrr_cnty.append(
                        {'date': date}, 
                        ignore_index=True
                    )
                    missing_dates.append(date)

            if len(missing_dates) > 0:
                print(f"* !!!! actnow county {fips}/{mchrr} has {len(missing_dates)}/{len(date_vals)} missing dates but fixed!")
            
            # then we need to fill the NaN values
            df_actnow_mchrr_cnty.fillna(method="ffill", inplace=True)
            df_actnow_mchrr_cnty.fillna(0, inplace=True)
            df_actnow_mchrr.append(df_actnow_mchrr_cnty)
        
        # combine all of the dataframes
        df_actnow_mchrr = pd.concat(df_actnow_mchrr, ignore_index=True)

        # then sum all by the date
        # and the date will be used as the index
        df_actnow_mchrr = df_actnow_mchrr.groupby('date')[[
            'actuals.cases', 
            'actuals.deaths', 
            'actuals.vaccinationsInitiated', 
            'actuals.vaccinationsCompleted'
        ]].sum()

        # then check the cdc pvi data and merge
        df_cdcpvi_mchrr = []
        for fips in fipss:
            df_cdcpvi_mchrr_cnty = df_cdcpvi[df_cdcpvi['countyFIPS'] == fips].copy()
            missing_dates = []
            existing_dates = set(df_cdcpvi_mchrr_cnty.date.values)
            for date in date_vals:
                if date not in existing_dates:
                    # missing data is very common in actnow ...
                    df_cdcpvi_mchrr_cnty = df_cdcpvi_mchrr_cnty.append(
                        {'date': date}, 
                        ignore_index=True
                    )
                    missing_dates.append(date)

            if len(missing_dates) > 0:
                print(f"* !!!! cdcpvi county {fips}/{mchrr} has {len(missing_dates)}/{len(date_vals)} missing dates but fixed!")

            # then we need to fill the NaN values
            df_cdcpvi_mchrr_cnty.fillna(method="ffill", inplace=True)
            df_cdcpvi_mchrr_cnty.fillna(0, inplace=True)
            df_cdcpvi_mchrr.append(df_cdcpvi_mchrr_cnty)

        # combine all of the dataframes
        df_cdcpvi_mchrr = pd.concat(df_cdcpvi_mchrr, ignore_index=True)

        # then get the median all by the date
        # and the date will be used as the index
        df_cdcpvi_mchrr = df_cdcpvi_mchrr.groupby('date')[[
            'pvi',
        ]].median()


        # for all date, get the values, start from 14 day
        for i in range(cfg.START_DATE_IDX, len(date_vals)):
            date_val = date_vals[i]

            # get the basics
            ncc = df_actnow_mchrr.loc[date_val, 'actuals.cases']
            dnc = ncc - df_actnow_mchrr.loc[date_vals[i-1], 'actuals.cases']
            d7v = (ncc - df_actnow_mchrr.loc[date_vals[i-7], 'actuals.cases']) / 7
            npp = ncc / pop * cfg.N_PERCAPITA
            dpp = dnc / pop * cfg.N_PERCAPITA
            d7p = d7v / pop * cfg.N_PERCAPITA

            # get the Death rate
            dth = df_actnow_mchrr.loc[date_val, 'actuals.deaths']
            try: dtr = dth / ncc
            except: dtr = 0

            # get the CDT
            _ncc_past = df_actnow_mchrr.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'actuals.cases']
            cdt = ds_util._calc_cdt(ncc, _ncc_past)

            # get the crrw ratio
            crp = d7p
            _ncc_7 = df_actnow_mchrr.loc[date_vals[i-7], 'actuals.cases']
            # get the past ncc
            try: _ncc_14 = df_actnow_mchrr.loc[date_vals[i-14], 'actuals.cases']
            except: _ncc_14 = 0
            # get the crt
            crt = ds_util._calc_crt(ncc, _ncc_7, _ncc_14)

            # get the cri of today
            cri = 2
            # the GREEN potential
            if crp <= cfg.S_GREEN_CRP_CUT_VALUE_1: cri = 1
            if crt <=1 and crp <= cfg.S_GREEN_CRP_CUT_VALUE_2: cri = 1

            # the RED potential
            if crt > cfg.S_RED_RW_CUT_VALUE_1 and crp > cfg.S_RED_CRP_CUT_VALUE_1: cri = 3
            if crp > cfg.S_RED_CRP_CUT_VALUE_2: cri = 3

            # get the crv of today
            crv = 0
            if i >= 7 + cfg.START_DATE_IDX:
                for j in range(1, 7+1):
                    crv += cris[i - cfg.START_DATE_IDX - j]
            
            # get the crc based on crv
            crc = 'Y'
            if crv <= 7: crc = 'G'
            if crv >=21: crc = 'R'

            pvi = df_cdcpvi_mchrr.loc[date_val, 'pvi']

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)

            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)
            
            dths.append(dth)
            dtrs.append(dtr)

            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)

            dates.append(date_val)

        # create JSON for this county
        j_county = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,
            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,
            
            'crps': crps,
            'crts': crts,
            'crcs': crcs,

            'pvis': pvis,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'MCHRR-%s.json' % FIPS
        )
        with open(fn, 'w') as fp:
            json.dump(j_county, fp, cls=NpEncoder)

        print('* parsed %s data %s' % (mchrr, parse_date))

    print('* done parsing all the MCHRR data %s from ACTNOW+CDCPVI' % (parse_date))


def parse_mchrr_with_cdcpvi_data_v2(parse_date=None):
    '''
    Deprecated.
    Parse MCHRR data for given parse_date with CDCPVI data

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - dths: deaths
        - dtrs: death rate
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index?
        - dates: dates of the data

    And the characteristics
        - state
        - FIPS
        - pop
        - name
        - date
    '''

    # get the date if it's None
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)
        print('* got parse_date=%s from input' % parse_date)

    print("""
    ###############################################################
    # Parse CDCPVI data %s to generate MCHRR-level results
    ###############################################################
    """ % (parse_date))
    
    # create the dates for parsing
    date_vals = []
    
    # get all dates
    dates = pd.date_range(cfg.FIRST_DATE, parse_date)
    for i in range(len(dates)):
        day = dates[i]
        date_vals.append(day.strftime('%Y-%m-%d'))
    print('* created dates %s to %s' % (date_vals[0], date_vals[-1]))

    # add MCHRR label
    mc_region_list = [
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
    mc_region_list.append({
        "name": "AVG", 
        "fips": list(set(reduce(lambda a, b: { 'fips': a['fips'] + b['fips'] }, mc_region_list)['fips']))
    })
    mchrrs = [ _['name'] for _ in mc_region_list ]
    
    # get the covid data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)

    # set index
    df_cdcpvi.set_index(['date', 'countyFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get population data
    df_pop = pd.read_csv(cfg.FN_COUNTY_POPU)
    print('* loaded population data from %s' % cfg.FN_COUNTY_POPU)

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        pass
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))


    for _ in tqdm(mc_region_list):
        mchrr = _['name']
        fipss = _['fips']

        # get basic characteristics
        FIPS = mchrr
        state = mchrr
        name = mchrr

        pop = df_pop[df_pop['FIPS'].isin(fipss)]['POP'].sum()

        # get other values
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        dths = []
        dtrs = []
        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []

        dates = []
        
        # for all date, get the values, start from 7 day
        for i in range(cfg.START_DATE_IDX, len(date_vals)):
            date_val = date_vals[i]

            # get the basics
            ncc = df_cdcpvi.loc[[(date_val, _) for _ in fipss], 'cases'].sum()
            dnc = ncc - df_cdcpvi.loc[[(date_vals[i-1], _) for _ in fipss], 'cases'].sum()
            d7v = (ncc - df_cdcpvi.loc[[(date_vals[i-7], _) for _ in fipss], 'cases'].sum()) / 7
            npp = ncc / pop * cfg.N_PERCAPITA
            dpp = dnc / pop * cfg.N_PERCAPITA
            d7p = d7v / pop * cfg.N_PERCAPITA

            # get the Death rate
            dth = df_cdcpvi.loc[[(date_val, _) for _ in fipss], 'deaths'].sum()
            try: dtr = dth / ncc
            except: dtr = 0

            # get the CDT
            _ncc_past = df_cdcpvi.loc[[ (date_vals[i-cfg.N_CDT_SMOOTH_DAYS], _) for _ in fipss ], 'cases'].sum()
            cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

            # get the crrw ratio
            crp = d7p
            _ncc_7 = df_cdcpvi.loc[[(date_vals[i-7], _) for _ in fipss], 'cases'].sum()
            # get the past ncc
            try: _ncc_14 = df_cdcpvi.loc[[(date_vals[i-14], _) for _ in fipss], 'cases'].sum()
            except: _ncc_14 = 0
            # get the crt
            try: crt = (ncc - _ncc_7) / (_ncc_7 - _ncc_14)
            except: crt = 0

            # get the cri of today
            cri = 2
            # the GREEN potential
            if crp <= cfg.S_GREEN_CRP_CUT_VALUE_1: cri = 1
            if crt <=1 and crp <= cfg.S_GREEN_CRP_CUT_VALUE_2: cri = 1

            # the RED potential
            if crt > cfg.S_RED_RW_CUT_VALUE_1 and crp > cfg.S_RED_CRP_CUT_VALUE_1: cri = 3
            if crp > cfg.S_RED_CRP_CUT_VALUE_2: cri = 3

            # get the crv of today
            crv = 0
            if i >= 7 + cfg.START_DATE_IDX:
                for j in range(1, 7+1):
                    crv += cris[i - cfg.START_DATE_IDX - j]
            
            # get the crc based on crv
            crc = 'Y'
            if crv <= 7: crc = 'G'
            if crv >=21: crc = 'R'

            pvi = df_cdcpvi.loc[[(date_val, _) for _ in fipss], 'pvi'].median()

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)

            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)
            
            dths.append(dth)
            dtrs.append(dtr)

            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)
            
