#!/usr/bin/env python3

# Copyright (c) Huan He (He.Huan@mayo.edu)
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

#%% load packages
import os
import sys
import math
import json
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

from ds_parser_mchrr import parse_mchrr_with_actnow_and_cdcpvi_data_v2
from ds_parser_country import parse_country_with_jhu_and_owid_data_v2
from ds_parser_state import parse_state_with_jhu_and_cdcpvi_and_actnow_v2
from ds_parser_state import parse_state_with_cdcpvi_and_actnow_v2
from ds_parser_county import parse_county_with_actnow_and_cdcpvi_data_v2

print('* loaded packages!')

# for solving the int64 serialization
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


# for multiprocessing

if sys.version_info.minor < 8:
    def istarmap(self, func, iterable, chunksize=1):
        """starmap-version of imap
        """
        if self._state != mpp.RUN:
            raise ValueError("Pool not running")

        if chunksize < 1:
            raise ValueError(
                "Chunksize must be 1+, not {0:n}".format(
                    chunksize))

        task_batches = mpp.Pool._get_tasks(func, iterable, chunksize)
        result = mpp.IMapIterator(self._cache)
        self._taskqueue.put(
            (
                self._guarded_task_generation(result._job,
                                            mpp.starmapstar,
                                            task_batches),
                result._set_length
            ))
        return (item for chunk in result for item in chunk)

    mpp.Pool.istarmap = istarmap

else:
    def istarmap(self, func, iterable, chunksize=1):
        """starmap-version of imap
        """
        self._check_running()
        if chunksize < 1:
            raise ValueError(
                "Chunksize must be 1+, not {0:n}".format(
                    chunksize))

        task_batches = mpp.Pool._get_tasks(func, iterable, chunksize)
        result = mpp.IMapIterator(self)
        self._taskqueue.put(
            (
                self._guarded_task_generation(result._job,
                                            mpp.starmapstar,
                                            task_batches),
                result._set_length
            ))
        return (item for chunk in result for item in chunk)

    mpp.Pool.istarmap = istarmap


def _floor(v):
    if pd.isna(v):
        return 0
    try:
        return math.floor(v)
    except:
        return 0


def _round(v, d=4):
    if pd.isna(v):
        return 0
    if np.isinf(v):
        return 0
    try:
        return round(v, d)
    except:
        return 0


#%% define data 

###############################################################################
# The parse functions v2
###############################################################################

def parse_county_with_usafacts_and_cdcpvi_data_v2(parse_date=None):
    '''
    Parse county data for given parse_date with USAFacts data

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - fgcs: flags for cases
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
    # Parse USAFacts + CDC %s to generate county-level results
    ###############################################################
    """ % (parse_date))
    
    # create the dates for parsing
    date_vals = []
    date_cols = []
    # +7 for the 7 day average calculation
    for i in range(cfg.N_DATES + 7):
        day = yesterday - datetime.timedelta(days=i)
        date_vals.append(day.strftime('%Y-%m-%d'))
        date_cols.append(day.strftime('%-m/%-d/%y'))

    # reverse the array for output
    date_vals.reverse()
    date_cols.reverse()
    print('* created dates %s to %s' % (date_vals[0], date_vals[-1]))

    # open the covid file
    fn_covid_data = cfg.FN_SAVE_USAFACTS_COUNTY_COVID_DATA % parse_date
    df_covid = pd.read_csv(fn_covid_data)
    df_covid.set_index('countyFIPS', inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_covid), fn_covid_data))

    # open the death file
    fn_death_data = cfg.FN_SAVE_USAFACTS_COUNTY_DEATH_DATA % parse_date
    df_death = pd.read_csv(fn_death_data)
    df_death.set_index('countyFIPS', inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_death), fn_death_data))

    # merge population data
    pop_data = pd.read_csv(cfg.FN_COUNTY_POPU)
    pop_data.set_index('FIPS', inplace=True)
    dft = df_covid.merge(pop_data.loc[:, ['POP']],
        left_index=True, right_index=True)
    print('* loaded population data from %s' % cfg.FN_COUNTY_POPU)

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        pass
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # begin loop on each county
    for idx, row in tqdm(dft.iterrows()):
        # get basic characteristics
        state = row['State']
        FIPS = idx
        FIPS = '%s' % FIPS if FIPS > 9999 else '0%s' % FIPS
        name = row['countyName']
        name = name.replace(' County', '')

        # fix for Washington D.C.
        if FIPS == '11001': name = "Washington, D.C."

        # get the pop
        pop = row['POP']

        # get other values
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []
        fgcs = []
        dates = []
        for i in range(7, cfg.N_DATES + 7):
            date_val = date_vals[i]
            date_col = date_cols[i]

            # get values
            ncc = row[date_col]
            dnc = ncc - row[date_cols[i - 1]]
            d7v = math.floor(( ncc - row[date_cols[i - 7]] ) / 7)
            npp = math.floor(ncc / pop * cfg.N_PERCAPITA)
            dpp = math.floor(dnc / pop * cfg.N_PERCAPITA)
            d7p = round(d7v / pop * cfg.N_PERCAPITA, 4)
            fgc = 0

            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)
            fgcs.append(fgc)
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
            'fgcs': fgcs,
            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, '%s.json' % FIPS
        )
        with open(fn, 'w') as fp:
            json.dump(j_county, fp, cls=NpEncoder)
        
        # print('* parsed %s / %s %s' % (idx, len(dft), FIPS))

    print('* done parsing all the county data %s from USAFacts' % (parse_date))


def __parse_county_with_cdcpvi_data_v2(
    df_cdcpvi_county, df_geo, df_pop, 
    date_vals, 
    countyFIPS, ):

    parse_date = date_vals[-1]

    # check if county exists
    if countyFIPS not in df_geo.index:
        print('* NOT found %s in geo data?' % countyFIPS)
        return -1

    if countyFIPS not in df_pop.index:
        print('* NOT found %s in pop data?' % countyFIPS)
        return -2

    # get basic characteristics
    FIPS = '%s' % countyFIPS if countyFIPS > 9999 else '0%s' % countyFIPS
    state = df_geo.loc[countyFIPS, 'state']
    lat = df_geo.loc[countyFIPS, 'lat']
    lon = df_geo.loc[countyFIPS, 'lon']
    name = df_pop.loc[countyFIPS, 'CNTYNAME']
    pop = df_pop.loc[countyFIPS, 'POP']

    # fix for Washington D.C.
    if FIPS == '11001': name = "Washington, D.C."

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
    for i in range(7, len(date_vals)):
        date_val = date_vals[i]

        # get the basics
        ncc = df_cdcpvi_county.loc[date_val, 'cases']
        dnc = ncc - df_cdcpvi_county.loc[date_vals[i-1], 'cases']
        d7v = (ncc - df_cdcpvi_county.loc[date_vals[i-7], 'cases']) / 7
        npp = ncc / pop * cfg.N_PERCAPITA
        dpp = dnc / pop * cfg.N_PERCAPITA
        d7p = d7v / pop * cfg.N_PERCAPITA

        # get the Death rate
        dth = df_cdcpvi_county.loc[date_val, 'deaths']
        try: dtr = dth / ncc
        except: dtr = 0

        # get the CDT
        _ncc_past = df_cdcpvi_county.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'cases']
        cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

        # get the crrw ratio
        crp = d7p
        _ncc_7 = df_cdcpvi_county.loc[date_vals[i-7], 'cases']
        # get the past ncc
        try: _ncc_14 = df_cdcpvi_county.loc[date_vals[i-14], 'cases']
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
        if i >= 7 + 7:
            for j in range(1, 7+1):
                crv += cris[i - 7 - j]
        
        # get the crc based on crv
        crc = 'Y'
        if crv <= 7: crc = 'G'
        if crv >=21: crc = 'R'

        pvi = df_cdcpvi_county.loc[date_val, 'pvi']

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
        'lat': lat,
        'lon': lon,

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
        # 'cris': cris,
        # 'crvs': crvs,
        'crcs': crcs,

        'pvis': pvis,

        'dates': dates
    }

    # save this json
    fn = os.path.join(
        cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % FIPS
    )
    with open(fn, 'w') as fp:
        json.dump(j_county, fp, cls=NpEncoder)

    return 0


def parse_county_with_cdcpvi_data_v2(parse_date=None):
    '''
    Parse county data for given parse_date with CDCPVI data

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
        - lat
        - lon
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
    # Parse CDCPVI data %s to generate county-level results
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

    # get the covid data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)

    # get all the counties
    counties = df_cdcpvi['countyFIPS'].unique().tolist()
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get population data
    df_pop = pd.read_csv(cfg.FN_COUNTY_POPU)
    df_pop.set_index('FIPS', inplace=True)
    print('* loaded population data from %s' % cfg.FN_COUNTY_POPU)

    # get the geo data
    df_geo = pd.read_csv(cfg.FN_COUNTY_GEO)
    df_geo.set_index('countyFIPS', inplace=True)
    print('* loaded geo data from %s' % cfg.FN_COUNTY_GEO)

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        pass
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # begin loop on each county
    # for countyFIPS in tqdm(counties):
    #     df_cdcpvi_county = df_cdcpvi[df_cdcpvi['countyFIPS']==countyFIPS]
    #     df_cdcpvi_county.set_index('date', inplace=True)
    #     __parse_county_with_cdcpvi_data_v2(df_cdcpvi_county, df_geo, df_pop, 
    #         date_vals, countyFIPS)

    # begin the multiprocessing
    with multiprocessing.Pool() as pool:
        arguments_list = [ ]
        for _fips in counties:
            df_cdcpvi_county = df_cdcpvi[df_cdcpvi['countyFIPS']==_fips]
            df_cdcpvi_county.set_index('date', inplace=True) 
            arguments_list.append((
                df_cdcpvi_county, df_geo, df_pop, date_vals, _fips
            ))
        for _ in tqdm(pool.istarmap( \
            func=__parse_county_with_cdcpvi_data_v2, \
            iterable=arguments_list \
            ), total=len(counties)):
            pass
    

    # for result in tqdm(pool.imap_unordered(func=func, iterable=argument_list), total=len(argument_list)):
    #     result_list_tqdm.append(result)


    print('* done parsing all the county data %s from CDC PVI' % (parse_date))




def __parse_county_with_cdcpvi_and_actnow_data_v2(
    df_cdcpvi_county, df_actnow_county, df_geo, df_pop, 
    date_vals, 
    countyFIPS, ):
    '''
    Maily based on CDC PVI Data
    '''

    parse_date = date_vals[-1]

    # there are missing in the actnow data, fill the missing
    df_actnow_county.sort_values(by=['date'], inplace=True)
    df_actnow_county.set_index('date', inplace=True)
    df_actnow_county.fillna(method="ffill", inplace=True)

    # check if county exists
    if countyFIPS not in df_geo.index:
        print('* NOT found %s in geo data?' % countyFIPS)
        return -1

    if countyFIPS not in df_pop.index:
        print('* NOT found %s in pop data?' % countyFIPS)
        return -2

    # get basic characteristics
    FIPS = '%s' % countyFIPS if countyFIPS > 9999 else '0%s' % countyFIPS
    state = df_geo.loc[countyFIPS, 'state']
    lat = df_geo.loc[countyFIPS, 'lat']
    lon = df_geo.loc[countyFIPS, 'lon']
    name = df_pop.loc[countyFIPS, 'CNTYNAME']
    pop = df_pop.loc[countyFIPS, 'POP']

    # fix for Washington D.C.
    if FIPS == '11001': name = "Washington, D.C."

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

    fvcs = []
    fvps = []
    vacs = []
    vaps = []

    dates = []
    
    # for all date, get the values, start from 7 day
    for i in range(7, len(date_vals)):
        date_val = date_vals[i]

        # get the basics
        ncc = df_cdcpvi_county.loc[date_val, 'cases']
        dnc = ncc - df_cdcpvi_county.loc[date_vals[i-1], 'cases']
        d7v = (ncc - df_cdcpvi_county.loc[date_vals[i-7], 'cases']) / 7
        npp = ncc / pop * cfg.N_PERCAPITA
        dpp = dnc / pop * cfg.N_PERCAPITA
        d7p = d7v / pop * cfg.N_PERCAPITA

        # get the Death rate
        dth = df_cdcpvi_county.loc[date_val, 'deaths']
        try: dtr = dth / ncc
        except: dtr = 0

        # get the CDT
        _ncc_past = df_cdcpvi_county.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'cases']
        cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

        # get the crrw ratio
        crp = d7p
        _ncc_7 = df_cdcpvi_county.loc[date_vals[i-7], 'cases']
        # get the past ncc
        try: _ncc_14 = df_cdcpvi_county.loc[date_vals[i-14], 'cases']
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
        if i >= 7 + 7:
            for j in range(1, 7+1):
                crv += cris[i - 7 - j]
        
        # get the crc based on crv
        crc = 'Y'
        if crv <= 7: crc = 'G'
        if crv >=21: crc = 'R'

        # get the PVI
        pvi = df_cdcpvi_county.loc[date_val, 'pvi']

        # get the FVC and FVP
        try:
            fvc = df_actnow_county.loc[date_val, 'actuals.vaccinationsCompleted']
            if pd.isna(fvc):
                fvc = 0
                fvp = 0
            else:
                fvp = fvc / pop
        except:
            fvc = 0
            fvp = 0
            
        # get the VAC and VAP
        try:
            vac = df_actnow_county.loc[date_val, 'actuals.vaccinationsInitiated']
        
            if pd.isna(vac):
                vac = 0
                vap = 0
            else:
                vap = vac / pop

        except:
            vac = 0
            vap = 0

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

        fvc = _floor(fvc)
        fvp = _round(fvp, 4)
        vac = _floor(vac)
        vap = _round(vap, 4)

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

        fvcs.append(fvc)
        fvps.append(fvp)
        vacs.append(vac)
        vaps.append(vap)


        dates.append(date_val)

    # create JSON for this county
    j_county = {
        'state': state,
        'FIPS': FIPS,
        'pop': pop,
        'name': name,
        'date': parse_date,
        'lat': lat,
        'lon': lon,

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
        # 'cris': cris,
        # 'crvs': crvs,
        'crcs': crcs,

        'pvis': pvis,

        'fvcs': fvcs,
        'fvps': fvps,
        'vacs': vacs,
        'vaps': vaps,

        'dates': dates
    }

    # save this json
    fn = os.path.join(
        cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % FIPS
    )
    with open(fn, 'w') as fp:
        json.dump(j_county, fp, cls=NpEncoder)

    return 0


def parse_county_with_jhu_and_cdcpvi_data_v2(parse_date=None):
    pass



def parse_state_with_covidtracking_and_cdcpvi_data_v2(parse_date=None):
    '''Parse state data for given parse_date

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - tprs: test positive rate
        - ttrs: total tests
        - tpts: total positive tests
        - t7rs: 7-day average test positive rate
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
    # Parse COVID Tracking Data %s to generate state-level results
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

    # get the covid data and pvi data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)
    df_cdcpvi['stateFIPS'] = df_cdcpvi['countyFIPS'] // 1000
    # df_cdcpvi.set_index(['date', 'stateFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get the covid data
    fn_data = cfg.FN_SAVE_COVIDTRACKING_STATE_DATA % parse_date
    df_ct = pd.read_csv(fn_data)

    # get all states
    states = df_ct['state'].unique().tolist()

    # set comb-index for this df
    # df_ct.set_index(['date', 'state'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_ct), fn_data))

    # get geo data
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)
    df_geo.set_index('stateAbbr', inplace=True)
    print('* loaded %s lines of state geo and fips' % (len(df_geo)))

    # get population data
    df_pop = pd.read_csv(cfg.FN_STATE_POPU)
    df_pop.set_index('ABBR', inplace=True)
    print('* loaded %s lines of state population and fips' % (len(df_pop)))

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        print('* found %s folder in %s' % (parse_date, cfg.FOLDER_PRS))
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # loop
    for state in tqdm(states):
        # get basic info
        stateFIPS = df_pop.loc[state, 'FIPS']
        FIPS = '%s' % stateFIPS if stateFIPS > 9 else '0%s' % stateFIPS
        name = df_pop.loc[state, 'NAME']
        pop = df_pop.loc[state, 'POP']
        lat = df_geo.loc[state, 'lat']
        lon = df_geo.loc[state, 'lon']

        # slice the df
        df_ct_state = df_ct[df_ct['state']==state]
        df_ct_state.set_index('date', inplace=True)
        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS]
        df_cdcpvi_state.set_index('date', inplace=True)

        # get the value
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        tprs = []
        ttrs = []
        tpts = []
        t7rs = []

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
            # get the date
            date_val = date_vals[i]

            if date_vals[i-7] in df_ct_state.index:
                ncc = df_ct_state.loc[date_val, 'positive']
                dnc = ncc - df_ct_state.loc[date_vals[i-1], 'positive']
                d7v = (ncc - df_ct_state.loc[date_vals[i-7], 'positive']) / 7

                npp = ncc / pop * cfg.N_PERCAPITA
                dpp = dnc / pop * cfg.N_PERCAPITA
                d7p = d7v / pop * cfg.N_PERCAPITA

                ttr = df_ct_state.loc[date_val, 'totalTestResults']
                tpt = df_ct_state.loc[date_val, 'positive']
                tpr = 0 if ttr == 0 else tpt / ttr
                dth = df_ct_state.loc[date_val, 'death']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = df_ct_state.loc[date_vals[i-7], 'totalTestResults']
                _tpt7 = df_ct_state.loc[date_vals[i-7], 'positive']
                t7r = 0 if (ttr - _ttr7) == 0 else (ncc - _tpt7) / (ttr - _ttr7)

                # get the CDT
                _ncc_past = df_ct_state.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'positive']
                cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

                # get the crrw ratio
                crp = d7p
                _ncc_7 = df_ct_state.loc[date_vals[i-7], 'positive']
                # get the past ncc
                try: _ncc_14 = df_ct_state.loc[date_vals[i-14], 'positive']
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
                        crv += cris[i-cfg.START_DATE_IDX-j]
                
                # get the crc based on crv
                crc = 'Y'
                if crv <= 7: crc = 'G'
                if crv >=21: crc = 'R'

                # get the PVI as median value of this state
                try: pvi = df_cdcpvi_state.loc[date_val, 'pvi'].median()
                except: pvi = 0

            else:
                # which means the no data? so, everything is 0
                ncc = 0
                dnc = 0
                d7v = 0
                npp = 0
                dpp = 0
                d7p = 0

                dth = 0
                dtr = 0

                tpr = 0
                ttr = 0
                tpt = 0
                t7r = 0

                cdt = cfg.CDT_CUT_VALUE

                crp = 0
                crt = 0
                cri = 0
                crv = 0
                crc = 'G'

                pvi = 0


            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            tpr = _round(tpr, 4)
            ttr = _floor(ttr)
            tpt = _floor(tpt)
            t7r = _round(t7r, 4)

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

            ttrs.append(ttr)
            tpts.append(tpt)
            tprs.append(tpr)
            t7rs.append(t7r)
            
            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)

            dates.append(date_val)

        # create JSON for this state
        j_state = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,
            'lat': lat,
            'lon': lon,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,

            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'tprs': tprs,
            'ttrs': ttrs,
            'tpts': tpts,
            't7rs': t7rs,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,

            'crps': crps,
            'crts': crts,
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'pvis': pvis,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % state
        )
        with open(fn, 'w') as fp:
            json.dump(j_state, fp, cls=NpEncoder)

    print('* done parsing the state data from covid tracking project data %s' % (parse_date))


def parse_state_with_covidtracking_and_cdcpvi_and_jhucci_data_v2(parse_date=None):
    '''
    Parse state data for given parse_date

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - tprs: test positive rate
        - ttrs: total tests
        - tpts: total positive tests
        - t7rs: 7-day average test positive rate
        - dths: deaths
        - dtrs: death rate        
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index? (from CDCPVI)
        - fvps: Fully Vaccinated Percentage
        - fvcs: Fully Vaccinated Count
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
    # Parse COVID Tracking Data %s to generate state-level results
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

    # get the covid data and pvi data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)
    df_cdcpvi['stateFIPS'] = df_cdcpvi['countyFIPS'] // 1000
    # df_cdcpvi.set_index(['date', 'stateFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get the covid data
    fn_data = cfg.FN_SAVE_COVIDTRACKING_STATE_DATA % parse_date
    df_ct = pd.read_csv(fn_data)

    # get the vaccination data
    fn_jhucci_vax = cfg.FN_SAVE_JHUCCI_STATE_VAX_DATA % parse_date
    df_jhucci_vax = pd.read_csv(fn_jhucci_vax)

    # get all states
    states = df_ct['state'].unique().tolist()

    # set comb-index for this df
    # df_ct.set_index(['date', 'state'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_ct), fn_data))

    # get geo data
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)
    df_geo.set_index('stateAbbr', inplace=True)
    print('* loaded %s lines of state geo and fips' % (len(df_geo)))

    # get population data
    df_pop = pd.read_csv(cfg.FN_STATE_POPU)
    df_pop.set_index('ABBR', inplace=True)
    print('* loaded %s lines of state population and fips' % (len(df_pop)))

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        print('* found %s folder in %s' % (parse_date, cfg.FOLDER_PRS))
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # loop
    for state in tqdm(states):
        # get basic info
        stateFIPS = df_pop.loc[state, 'FIPS']
        FIPS = '%s' % stateFIPS if stateFIPS > 9 else '0%s' % stateFIPS
        name = df_pop.loc[state, 'NAME']
        pop = df_pop.loc[state, 'POP']
        lat = df_geo.loc[state, 'lat']
        lon = df_geo.loc[state, 'lon']

        # slice the df
        df_ct_state = df_ct[df_ct['state']==state]
        df_ct_state.set_index('date', inplace=True)
        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS]
        df_cdcpvi_state.set_index('date', inplace=True)
        df_jhucci_vax_state = df_jhucci_vax[df_jhucci_vax['stabbr']==state]
        df_jhucci_vax_state.set_index('date', inplace=True)

        # get the value
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        tprs = []
        ttrs = []
        tpts = []
        t7rs = []

        dths = []
        dtrs = []

        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []
        fvcs = []
        fvps = []

        dates = []

        # for all date, get the values, start from 7 day
        for i in range(cfg.START_DATE_IDX, len(date_vals)):
            # get the date
            date_val = date_vals[i]

            if date_vals[i-7] in df_ct_state.index:
                ncc = df_ct_state.loc[date_val, 'positive']
                dnc = ncc - df_ct_state.loc[date_vals[i-1], 'positive']
                d7v = (ncc - df_ct_state.loc[date_vals[i-7], 'positive']) / 7

                npp = ncc / pop * cfg.N_PERCAPITA
                dpp = dnc / pop * cfg.N_PERCAPITA
                d7p = d7v / pop * cfg.N_PERCAPITA

                ttr = df_ct_state.loc[date_val, 'totalTestResults']
                tpt = df_ct_state.loc[date_val, 'positive']
                tpr = 0 if ttr == 0 else tpt / ttr
                dth = df_ct_state.loc[date_val, 'death']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = df_ct_state.loc[date_vals[i-7], 'totalTestResults']
                _tpt7 = df_ct_state.loc[date_vals[i-7], 'positive']
                t7r = 0 if _ttr7 == 0 else _tpt7 / _ttr7

                # get the CDT
                _ncc_past = df_ct_state.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'positive']
                cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

                # get the crrw ratio
                crp = d7p
                _ncc_7 = df_ct_state.loc[date_vals[i-7], 'positive']
                # get the past ncc
                try: _ncc_14 = df_ct_state.loc[date_vals[i-14], 'positive']
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
                        crv += cris[i-cfg.START_DATE_IDX-j]
                
                # get the crc based on crv
                crc = 'Y'
                if crv <= 7: crc = 'G'
                if crv >=21: crc = 'R'

                # get the PVI as median value of this state
                try: pvi = df_cdcpvi_state.loc[date_val, 'pvi'].median()
                except: pvi = 0

                # get the FVP
                try:
                    fvc = df_jhucci_vax_state.loc[date_val, 'people_total_2nd_dose']
                    if pd.isna(fvc):
                        fvp = 0
                    else:
                        fvp = fvc / pop
                except:
                    fvc = 0
                    fvp = 0

            else:
                # which means the no data? so, everything is 0
                ncc = 0
                dnc = 0
                d7v = 0
                npp = 0
                dpp = 0
                d7p = 0

                dth = 0
                dtr = 0

                tpr = 0
                ttr = 0
                tpt = 0
                t7r = 0

                cdt = cfg.CDT_CUT_VALUE

                crp = 0
                crt = 0
                cri = 0
                crv = 0
                crc = 'G'

                pvi = 0
                fvc = 0
                fvp = 0

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            tpr = _round(tpr, 4)
            ttr = _floor(ttr)
            tpt = _floor(tpt)
            t7r = _round(t7r, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)
            fvc = _floor(fvc)
            fvp = _round(fvp, 4)
            
            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)

            dths.append(dth)
            dtrs.append(dtr)

            ttrs.append(ttr)
            tpts.append(tpt)
            tprs.append(tpr)
            t7rs.append(t7r)
            
            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)
            fvcs.append(fvc)
            fvps.append(fvp)

            dates.append(date_val)

        # create JSON for this state
        j_state = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,
            'lat': lat,
            'lon': lon,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,

            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'tprs': tprs,
            'ttrs': ttrs,
            'tpts': tpts,
            't7rs': t7rs,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,

            'crps': crps,
            'crts': crts,
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'pvis': pvis,
            'fvcs': fvcs,
            'fvps': fvps,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % state
        )
        with open(fn, 'w') as fp:
            json.dump(j_state, fp, cls=NpEncoder)

    print('* done parsing the state data from covid tracking project data %s' % (parse_date))


def parse_state_with_covidtracking_and_cdcpvi_and_jhucci_data_and_cdcvac_v2(parse_date=None):
    '''
    Parse state data for given parse_date

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - tprs: test positive rate
        - ttrs: total tests
        - tpts: total positive tests
        - t7rs: 7-day average test positive rate
        - dths: deaths
        - dtrs: death rate        
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index? (from CDCPVI)
        - fvps: Fully Vaccinated Percentage
        - fvcs: Fully Vaccinated Count
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
    # Parse COVID Tracking Data %s to generate state-level results
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

    # get the covid data and pvi data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)
    df_cdcpvi['stateFIPS'] = df_cdcpvi['countyFIPS'] // 1000
    # df_cdcpvi.set_index(['date', 'stateFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get the covid data
    fn_data = cfg.FN_SAVE_COVIDTRACKING_STATE_DATA % parse_date
    df_ct = pd.read_csv(fn_data)

    # get the vaccination data of JHU
    fn_jhucci_vax = cfg.FN_SAVE_JHUCCI_STATE_VAX_DATA % parse_date
    df_jhucci_vax = pd.read_csv(fn_jhucci_vax)

    # get the vaccination data of CDC
    fn_cdcvac = cfg.FN_SAVE_CDCVAC_STATE_VAC_DATA % parse_date
    df_cdcvac = pd.read_csv(fn_cdcvac)
    df_cdcvac.set_index('Location', inplace=True)

    # get all states
    states = df_ct['state'].unique().tolist()

    # set comb-index for this df
    # df_ct.set_index(['date', 'state'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_ct), fn_data))

    # get geo data
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)
    df_geo.set_index('stateAbbr', inplace=True)
    print('* loaded %s lines of state geo and fips' % (len(df_geo)))

    # get population data
    df_pop = pd.read_csv(cfg.FN_STATE_POPU)
    df_pop.set_index('ABBR', inplace=True)
    print('* loaded %s lines of state population and fips' % (len(df_pop)))

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        print('* found %s folder in %s' % (parse_date, cfg.FOLDER_PRS))
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # loop
    for state in tqdm(states):
        # get basic info
        stateFIPS = df_pop.loc[state, 'FIPS']
        FIPS = '%s' % stateFIPS if stateFIPS > 9 else '0%s' % stateFIPS
        name = df_pop.loc[state, 'NAME']
        pop = df_pop.loc[state, 'POP']
        lat = df_geo.loc[state, 'lat']
        lon = df_geo.loc[state, 'lon']

        # slice the df
        df_ct_state = df_ct[df_ct['state']==state]
        df_ct_state.set_index('date', inplace=True)
        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS]
        df_cdcpvi_state.set_index('date', inplace=True)
        df_jhucci_vax_state = df_jhucci_vax[df_jhucci_vax['stabbr']==state]
        df_jhucci_vax_state.set_index('date', inplace=True)

        # get the value
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        tprs = []
        ttrs = []
        tpts = []
        t7rs = []

        dths = []
        dtrs = []

        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []
        fvcs = []
        fvps = []

        dates = []

        # for all date, get the values, start from 7 day
        for i in range(cfg.START_DATE_IDX, len(date_vals)):
            # get the date
            date_val = date_vals[i]

            if date_vals[i-7] in df_ct_state.index:
                ncc = df_ct_state.loc[date_val, 'positive']
                dnc = ncc - df_ct_state.loc[date_vals[i-1], 'positive']
                d7v = (ncc - df_ct_state.loc[date_vals[i-7], 'positive']) / 7

                npp = ncc / pop * cfg.N_PERCAPITA
                dpp = dnc / pop * cfg.N_PERCAPITA
                d7p = d7v / pop * cfg.N_PERCAPITA

                ttr = df_ct_state.loc[date_val, 'totalTestResults']
                tpt = df_ct_state.loc[date_val, 'positive']
                tpr = 0 if ttr == 0 else tpt / ttr
                dth = df_ct_state.loc[date_val, 'death']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = df_ct_state.loc[date_vals[i-7], 'totalTestResults']
                _tpt7 = df_ct_state.loc[date_vals[i-7], 'positive']
                # t7r = 0 if _ttr7 == 0 else _tpt7 / _ttr7
                t7r = 0 if (ttr - _ttr7) == 0 else (ncc - _tpt7) / (ttr - _ttr7)

                # get the CDT
                _ncc_past = df_ct_state.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'positive']
                cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

                # get the crrw ratio
                crp = d7p
                _ncc_7 = df_ct_state.loc[date_vals[i-7], 'positive']
                # get the past ncc
                try: _ncc_14 = df_ct_state.loc[date_vals[i-14], 'positive']
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
                        crv += cris[i-cfg.START_DATE_IDX-j]
                
                # get the crc based on crv
                crc = 'Y'
                if crv <= 7: crc = 'G'
                if crv >=21: crc = 'R'

                # get the PVI as median value of this state
                try: pvi = df_cdcpvi_state.loc[date_val, 'pvi'].median()
                except: pvi = 0

                # get the FVP
                try:
                    fvc = df_jhucci_vax_state.loc[date_val, 'people_total_2nd_dose']
                    if pd.isna(fvc):
                        fvc = 0
                        fvp = 0
                    else:
                        fvp = fvc / pop
                except:
                    fvc = 0
                    fvp = 0

                # try the cdc vac data to update the JHU data last date
                if i == (len(date_vals) - 1):
                    try:
                        fvc2 = df_cdcvac.loc[state, 'Administered_Dose2']
                        if fvc2 > fvc:
                            fvc = fvc2
                            fvp = fvc2 / pop
                        else:
                            pass
                    except:
                        pass
                else:
                    pass

            else:
                # which means the no data? so, everything is 0
                ncc = 0
                dnc = 0
                d7v = 0
                npp = 0
                dpp = 0
                d7p = 0

                dth = 0
                dtr = 0

                tpr = 0
                ttr = 0
                tpt = 0
                t7r = 0

                cdt = cfg.CDT_CUT_VALUE

                crp = 0
                crt = 0
                cri = 0
                crv = 0
                crc = 'G'

                pvi = 0
                fvc = 0
                fvp = 0

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            tpr = _round(tpr, 4)
            ttr = _floor(ttr)
            tpt = _floor(tpt)
            t7r = _round(t7r, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)
            fvc = _floor(fvc)
            fvp = _round(fvp, 4)
            
            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)

            dths.append(dth)
            dtrs.append(dtr)

            ttrs.append(ttr)
            tpts.append(tpt)
            tprs.append(tpr)
            t7rs.append(t7r)
            
            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)
            fvcs.append(fvc)
            fvps.append(fvp)

            dates.append(date_val)

        # create JSON for this state
        j_state = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,
            'lat': lat,
            'lon': lon,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,

            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'tprs': tprs,
            'ttrs': ttrs,
            'tpts': tpts,
            't7rs': t7rs,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,

            'crps': crps,
            'crts': crts,
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'pvis': pvis,
            'fvcs': fvcs,
            'fvps': fvps,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % state
        )
        with open(fn, 'w') as fp:
            json.dump(j_state, fp, cls=NpEncoder)

    print('* done parsing the state data from covid tracking project data %s' % (parse_date))


def parse_state_with_actnow_and_cdcpvi_and_cdcvac_v2(parse_date=None):
    '''
    Deprecated
    Parse state data for given parse_date

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - tprs: test positive rate
        - ttrs: total tests
        - tpts: total positive tests
        - t7rs: 7-day average test positive rate
        - dths: deaths
        - dtrs: death rate        
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index? (from CDCPVI)
        - fvps: Fully Vaccinated Percentage
        - fvcs: Fully Vaccinated Count
        - vacs: Total number of doses administered
        - vaps: Total percentage of doses administered
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
    # Parse COVID Act Now Data %s to generate state-level results
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

    # get the covid data and pvi data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)
    df_cdcpvi['stateFIPS'] = df_cdcpvi['countyFIPS'] // 1000
    # df_cdcpvi.set_index(['date', 'stateFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get the covid data
    fn_data = cfg.FN_SAVE_ACTNOW_STATE_DATA % parse_date
    df_actnow = pd.read_csv(fn_data)

    # get the vaccination data of JHU
    fn_jhucci_vax = cfg.FN_SAVE_JHUCCI_STATE_VAX_DATA % parse_date
    df_jhucci_vax = pd.read_csv(fn_jhucci_vax)

    # get the vaccination data of CDC
    fn_cdcvac = cfg.FN_SAVE_CDCVAC_STATE_VAC_DATA % parse_date
    df_cdcvac = pd.read_csv(fn_cdcvac)
    df_cdcvac.set_index('Location', inplace=True)

    # get geo data
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)

    # get all states from local geo data
    states = df_geo.stateAbbr.unique().tolist()

    df_geo.set_index('stateAbbr', inplace=True)
    print('* loaded %s lines of state geo and fips' % (len(df_geo)))

    # get population data
    df_pop = pd.read_csv(cfg.FN_STATE_POPU)
    df_pop.set_index('ABBR', inplace=True)
    print('* loaded %s lines of state population and fips' % (len(df_pop)))

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        print('* found %s folder in %s' % (parse_date, cfg.FOLDER_PRS))
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # loop on state
    for state in tqdm(states):
        # get basic info
        stateFIPS = df_pop.loc[state, 'FIPS']
        FIPS = '%s' % stateFIPS if stateFIPS > 9 else '0%s' % stateFIPS
        name = df_pop.loc[state, 'NAME']
        pop = df_pop.loc[state, 'POP']
        lat = df_geo.loc[state, 'lat']
        lon = df_geo.loc[state, 'lon']

        # slice the df
        df_actnow_state = df_actnow[df_actnow['state']==state]
        df_actnow_state.set_index('date', inplace=True)
        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS]
        df_cdcpvi_state.set_index('date', inplace=True)
        df_jhucci_vax_state = df_jhucci_vax[df_jhucci_vax['stabbr']==state]
        df_jhucci_vax_state.set_index('date', inplace=True)

        # get the values
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        tprs = []
        ttrs = []
        tpts = []
        t7rs = []

        dths = []
        dtrs = []

        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []
        fvcs = []
        fvps = []
        vacs = []
        vaps = []

        dates = []

        # for all date, get the values, start from 7 day
        for i in range(cfg.START_DATE_IDX, len(date_vals)):
            # get the date
            date_val = date_vals[i]

            if date_vals[i-7] in df_actnow_state.index:
                ncc = df_actnow_state.loc[date_val, 'actuals.cases']
                dnc = ncc - df_actnow_state.loc[date_vals[i-1], 'actuals.cases']
                d7v = (ncc - df_actnow_state.loc[date_vals[i-7], 'actuals.cases']) / 7

                npp = ncc / pop * cfg.N_PERCAPITA
                dpp = dnc / pop * cfg.N_PERCAPITA
                d7p = d7v / pop * cfg.N_PERCAPITA

                ttr = None
                tpt = df_actnow_state.loc[date_val, 'actuals.cases']
                tpr = None
                dth = df_actnow_state.loc[date_val, 'actuals.deaths']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = None
                _tpt7 = df_actnow_state.loc[date_vals[i-7], 'actuals.cases']
                t7r = None

                # get the CDT
                _ncc_past = df_actnow_state.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'actuals.cases']
                cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

                # get the crrw ratio
                crp = d7p
                _ncc_7 = df_actnow_state.loc[date_vals[i-7], 'actuals.cases']
                # get the past ncc
                try: _ncc_14 = df_actnow_state.loc[date_vals[i-14], 'actuals.cases']
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
                        crv += cris[i-cfg.START_DATE_IDX-j]
                
                # get the crc based on crv
                crc = 'Y'
                if crv <= 7: crc = 'G'
                if crv >=21: crc = 'R'

                # get the PVI as median value of this state
                try: pvi = df_cdcpvi_state.loc[date_val, 'pvi'].median()
                except: pvi = 0

                # get the FVP
                try:
                    fvc = df_jhucci_vax_state.loc[date_val, 'people_total_2nd_dose']
                    if pd.isna(fvc):
                        fvc = 0
                        fvp = 0
                    else:
                        fvp = fvc / pop
                except:
                    fvc = 0
                    fvp = 0

                # try the cdc vac data to update the JHU data last date
                if i == (len(date_vals) - 1):
                    try:
                        fvc2 = df_cdcvac.loc[state, 'Administered_Dose2']
                        if fvc2 > fvc:
                            fvc = fvc2
                            fvp = fvc2 / pop
                        else:
                            pass
                    except:
                        pass
                else:
                    pass

                # get the VAP and VAC
                try:
                    vac = df_actnow_state.loc[date_val, 'actuals.vaccinationsInitiated']
                    vap = df_actnow_state.loc[date_val, 'metrics.vaccinationsInitiatedRatio']
                
                    if pd.isna(vac):
                        vac = 0
                    if pd.isna(vap):
                        vap = 0
                except:
                    vac = 0
                    vap = 0

            else:
                # which means the no data? so, everything is 0
                ncc = 0
                dnc = 0
                d7v = 0
                npp = 0
                dpp = 0
                d7p = 0

                dth = 0
                dtr = 0

                tpr = 0
                ttr = 0
                tpt = 0
                t7r = 0

                cdt = cfg.CDT_CUT_VALUE

                crp = 0
                crt = 0
                cri = 0
                crv = 0
                crc = 'G'

                pvi = 0
                fvc = 0
                fvp = 0
                vac = 0
                vap = 0

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            tpr = _round(tpr, 4)
            ttr = _floor(ttr)
            tpt = _floor(tpt)
            t7r = _round(t7r, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)
            fvc = _floor(fvc)
            fvp = _round(fvp, 4)
            vac = _floor(vac)
            vap = _round(vap, 4)
            
            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)

            dths.append(dth)
            dtrs.append(dtr)

            ttrs.append(ttr)
            tpts.append(tpt)
            tprs.append(tpr)
            t7rs.append(t7r)
            
            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)
            fvcs.append(fvc)
            fvps.append(fvp)
            vacs.append(vac)
            vaps.append(vap)

            dates.append(date_val)

        # create JSON for this state
        j_state = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,
            'lat': lat,
            'lon': lon,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,

            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'tprs': tprs,
            'ttrs': ttrs,
            'tpts': tpts,
            't7rs': t7rs,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,

            'crps': crps,
            'crts': crts,
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'pvis': pvis,
            'fvcs': fvcs,
            'fvps': fvps,
            'vacs': vacs,
            'vaps': vaps,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % state
        )
        with open(fn, 'w') as fp:
            json.dump(j_state, fp, cls=NpEncoder)

    print('* done parsing the state data from COVID Act Now data %s' % (parse_date))


def parse_state_with_jhu_and_jhucci_and_cdcpvi_and_cdcvac_v2(parse_date=None):
    '''
    Deprecated. Don't use this.

    Parse state data for given parse_date

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - tprs: test positive rate
        - ttrs: total tests
        - tpts: total positive tests
        - t7rs: 7-day average test positive rate
        - dths: deaths
        - dtrs: death rate        
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index? (from CDCPVI)
        - fvps: Fully Vaccinated Percentage
        - fvcs: Fully Vaccinated Count
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
    # Parse JHU Data %s to generate state-level results
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

    # get the covid data and pvi data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)
    df_cdcpvi['stateFIPS'] = df_cdcpvi['countyFIPS'] // 1000
    # df_cdcpvi.set_index(['date', 'stateFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get the covid data
    fn_data = cfg.FN_SAVE_JHU_STATE_ALL_DATA % parse_date
    df_jhu = pd.read_csv(fn_data)

    # get the vaccination data of JHU
    fn_jhucci_vax = cfg.FN_SAVE_JHUCCI_STATE_VAX_DATA % parse_date
    df_jhucci_vax = pd.read_csv(fn_jhucci_vax)

    # get the vaccination data of CDC
    fn_cdcvac = cfg.FN_SAVE_CDCVAC_STATE_VAC_DATA % parse_date
    df_cdcvac = pd.read_csv(fn_cdcvac)
    df_cdcvac.set_index('Location', inplace=True)

    # get geo data
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)

    # get all states from local geo data
    states = df_geo.stateAbbr.unique().tolist()

    df_geo.set_index('stateAbbr', inplace=True)
    print('* loaded %s lines of state geo and fips' % (len(df_geo)))

    # get population data
    df_pop = pd.read_csv(cfg.FN_STATE_POPU)
    df_pop.set_index('ABBR', inplace=True)
    print('* loaded %s lines of state population and fips' % (len(df_pop)))

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        print('* found %s folder in %s' % (parse_date, cfg.FOLDER_PRS))
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # loop on state
    for state in tqdm(states):
        # get basic info
        stateFIPS = df_pop.loc[state, 'FIPS']
        FIPS = '%s' % stateFIPS if stateFIPS > 9 else '0%s' % stateFIPS
        name = df_pop.loc[state, 'NAME']
        pop = df_pop.loc[state, 'POP']
        lat = df_geo.loc[state, 'lat']
        lon = df_geo.loc[state, 'lon']

        # slice the df
        df_jhu_state = df_jhu[df_jhu['state']==state]
        df_jhu_state.set_index('date', inplace=True)
        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS]
        df_cdcpvi_state.set_index('date', inplace=True)
        df_jhucci_vax_state = df_jhucci_vax[df_jhucci_vax['stabbr']==state]
        df_jhucci_vax_state.set_index('date', inplace=True)
        
        # get the values
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        tprs = []
        ttrs = []
        tpts = []
        t7rs = []

        dths = []
        dtrs = []

        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []
        fvcs = []
        fvps = []

        dates = []

        # for all date, get the values, start from 7 day
        for i in range(7, len(date_vals)):
            # get the date
            date_val = date_vals[i]

            if date_vals[i-7] in df_jhu_state.index:
                ncc = df_jhu_state.loc[date_val, 'cases']
                dnc = ncc - df_jhu_state.loc[date_vals[i-1], 'cases']
                d7v = (ncc - df_jhu_state.loc[date_vals[i-7], 'cases']) / 7

                npp = ncc / pop * cfg.N_PERCAPITA
                dpp = dnc / pop * cfg.N_PERCAPITA
                d7p = d7v / pop * cfg.N_PERCAPITA

                ttr = df_jhu_state.loc[date_val, 'totalTestResults']
                tpt = df_jhu_state.loc[date_val, 'cases']
                tpr = 0 if ttr == 0 else tpt / ttr
                dth = df_jhu_state.loc[date_val, 'deaths']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = df_jhu_state.loc[date_vals[i-7], 'totalTestResults']
                _tpt7 = df_jhu_state.loc[date_vals[i-7], 'cases']
                t7r = 0 if (ttr - _ttr7) == 0 else (ncc - _tpt7) / (ttr - _ttr7)

                # get the CDT
                _ncc_past = df_jhu_state.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'cases']
                cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

                # get the crrw ratio
                crp = d7p
                _ncc_7 = df_jhu_state.loc[date_vals[i-7], 'cases']
                # get the past ncc
                try: _ncc_14 = df_jhu_state.loc[date_vals[i-14], 'cases']
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
                if i >= 7 + 7:
                    for j in range(1, 7+1):
                        crv += cris[i-7-j]
                
                # get the crc based on crv
                crc = 'Y'
                if crv <= 7: crc = 'G'
                if crv >=21: crc = 'R'

                # get the PVI as median value of this state
                try: pvi = df_cdcpvi_state.loc[date_val, 'pvi'].median()
                except: pvi = 0

                # get the FVP
                try:
                    fvc = df_jhucci_vax_state.loc[date_val, 'people_total_2nd_dose']
                    if pd.isna(fvc):
                        fvc = 0
                        fvp = 0
                    else:
                        fvp = fvc / pop
                except:
                    fvc = 0
                    fvp = 0

                # try the cdc vac data to update the JHU data last date
                if i == (len(date_vals) - 1):
                    try:
                        fvc2 = df_cdcvac.loc[state, 'Administered_Dose2']
                        if fvc2 > fvc:
                            fvc = fvc2
                            fvp = fvc2 / pop
                        else:
                            pass
                    except:
                        pass
                else:
                    pass

            else:
                # which means the no data? so, everything is 0
                ncc = 0
                dnc = 0
                d7v = 0
                npp = 0
                dpp = 0
                d7p = 0

                dth = 0
                dtr = 0

                tpr = 0
                ttr = 0
                tpt = 0
                t7r = 0

                cdt = cfg.CDT_CUT_VALUE

                crp = 0
                crt = 0
                cri = 0
                crv = 0
                crc = 'G'

                pvi = 0
                fvc = 0
                fvp = 0

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            tpr = _round(tpr, 4)
            ttr = _floor(ttr)
            tpt = _floor(tpt)
            t7r = _round(t7r, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)
            fvc = _floor(fvc)
            fvp = _round(fvp, 4)
            
            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)

            dths.append(dth)
            dtrs.append(dtr)

            ttrs.append(ttr)
            tpts.append(tpt)
            tprs.append(tpr)
            t7rs.append(t7r)
            
            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)
            fvcs.append(fvc)
            fvps.append(fvp)

            dates.append(date_val)

        # create JSON for this state
        j_state = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,
            'lat': lat,
            'lon': lon,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,

            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'tprs': tprs,
            'ttrs': ttrs,
            'tpts': tpts,
            't7rs': t7rs,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,

            'crps': crps,
            'crts': crts,
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'pvis': pvis,
            'fvcs': fvcs,
            'fvps': fvps,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % state
        )
        with open(fn, 'w') as fp:
            json.dump(j_state, fp, cls=NpEncoder)

    print('* done parsing the state data from JHU data %s' % (parse_date))


def parse_state_with_jhu_and_cdcpvi_and_actnow_and_cdcvac_v2(parse_date=None):
    '''
    Deprecated
    Parse state data for given parse_date

    Args:
        parse_date: YYYY-MM-DD format date string

    Create:
        - nccs: total cases
        - dncs: daily cases
        - d7vs: 7-day average cases
        - npps: total cases per 100k
        - dpps: daily cases per 100k
        - d7ps: 7-day average cases per 100k
        - tprs: test positive rate
        - ttrs: total tests
        - tpts: total positive tests
        - t7rs: 7-day average test positive rate
        - dths: deaths
        - dtrs: death rate        
        - cdts: 4 day smoothed case doubling time
        - crps: Cr7d100k case rate
        - crts: RW_Cr7d100k case ratio
        - crcs: CrRW status
        - pvis: Pandemic V Index? (from CDCPVI)
        - fvps: Fully Vaccinated Percentage
        - fvcs: Fully Vaccinated Count
        - vacs: Total number of doses administered
        - vaps: Total percentage of doses administered
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
    ###########################################################################
    # Parse JHU+CDCPVI_ACTNOW Data %s to generate state-level results
    ###########################################################################
    """ % (parse_date))

    # create the dates for parsing
    date_vals = []

    # get all dates
    dates = pd.date_range(cfg.FIRST_DATE, parse_date)
    for i in range(len(dates)):
        day = dates[i]
        date_vals.append(day.strftime('%Y-%m-%d'))
    print('* created dates %s to %s' % (date_vals[0], date_vals[-1]))

    # get the covid data and pvi data
    fn_cdcpvi_data = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_cdcpvi = pd.read_csv(fn_cdcpvi_data)
    df_cdcpvi['stateFIPS'] = df_cdcpvi['countyFIPS'] // 1000
    # df_cdcpvi.set_index(['date', 'stateFIPS'], inplace=True)
    print('* loaded %s lines data frame from %s' % (len(df_cdcpvi), fn_cdcpvi_data))

    # get the covid data
    fn_data = cfg.FN_SAVE_JHU_STATE_ALL_DATA % parse_date
    df_jhu = pd.read_csv(fn_data)

    # get the vaccination data of JHU
    fn_actnow = cfg.FN_SAVE_ACTNOW_STATE_DATA % parse_date
    df_actnow = pd.read_csv(fn_actnow)

    # get the vaccination data of CDC
    fn_cdcvac = cfg.FN_SAVE_CDCVAC_STATE_VAC_DATA % parse_date
    df_cdcvac = pd.read_csv(fn_cdcvac)

    # get geo data
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)

    # get all states from local geo data
    states = df_geo.stateAbbr.unique().tolist()

    df_geo.set_index('stateAbbr', inplace=True)
    print('* loaded %s lines of state geo and fips' % (len(df_geo)))

    # get population data
    df_pop = pd.read_csv(cfg.FN_STATE_POPU)
    df_pop.set_index('ABBR', inplace=True)
    print('* loaded %s lines of state population and fips' % (len(df_pop)))

    # create parse date folder
    if os.path.exists(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date)):
        print('* found %s folder in %s' % (parse_date, cfg.FOLDER_PRS))
    else:
        os.makedirs(os.path.join(cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date), exist_ok=True)
        print('* created %s folder in %s' % (parse_date, cfg.FOLDER_PRS))

    # loop on state
    for state in tqdm(states):
        # get basic info
        stateFIPS = df_pop.loc[state, 'FIPS']
        FIPS = '%s' % stateFIPS if stateFIPS > 9 else '0%s' % stateFIPS
        name = df_pop.loc[state, 'NAME']
        pop = df_pop.loc[state, 'POP']
        lat = df_geo.loc[state, 'lat']
        lon = df_geo.loc[state, 'lon']

        # slice the df
        df_jhu_state = df_jhu[df_jhu['state']==state]
        df_jhu_state.set_index('date', inplace=True)
        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS]
        df_cdcpvi_state.set_index('date', inplace=True)
        df_actnow_state = df_actnow[df_actnow['state']==state]
        df_actnow_state.set_index('date', inplace=True)
        df_cdcvac_state = df_cdcvac[df_cdcvac['Location']==state]
        df_cdcvac_state.set_index('date', inplace=True)
        
        # get the values
        nccs = []
        dncs = []
        d7vs = []
        npps = []
        dpps = []
        d7ps = []

        tprs = []
        ttrs = []
        tpts = []
        t7rs = []

        dths = []
        dtrs = []

        cdts = []

        crps = []
        crts = []
        cris = []
        crvs = []
        crcs = []

        pvis = []
        fvcs = []
        fvps = []
        vacs = []
        vaps = []

        dates = []

        # for all date, get the values, start from 7 day
        for i in range(7, len(date_vals)):
            # get the date
            date_val = date_vals[i]

            if date_vals[i-7] in df_jhu_state.index:
                ncc = df_jhu_state.loc[date_val, 'cases']
                dnc = ncc - df_jhu_state.loc[date_vals[i-1], 'cases']
                d7v = (ncc - df_jhu_state.loc[date_vals[i-7], 'cases']) / 7

                npp = ncc / pop * cfg.N_PERCAPITA
                dpp = dnc / pop * cfg.N_PERCAPITA
                d7p = d7v / pop * cfg.N_PERCAPITA

                ttr = df_jhu_state.loc[date_val, 'totalTestResults']
                tpt = df_jhu_state.loc[date_val, 'cases']
                tpr = 0 if ttr == 0 else tpt / ttr
                dth = df_jhu_state.loc[date_val, 'deaths']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = df_jhu_state.loc[date_vals[i-7], 'totalTestResults']
                _tpt7 = df_jhu_state.loc[date_vals[i-7], 'cases']
                t7r = 0 if (ttr - _ttr7) == 0 else (ncc - _tpt7) / (ttr - _ttr7)

                # get the CDT
                _ncc_past = df_jhu_state.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'cases']
                cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

                # get the crrw ratio
                crp = d7p
                _ncc_7 = df_jhu_state.loc[date_vals[i-7], 'cases']
                # get the past ncc
                try: _ncc_14 = df_jhu_state.loc[date_vals[i-14], 'cases']
                except: _ncc_14 = 0
                # get the crt
                try: crt = (ncc - _ncc_7) / (_ncc_7 - _ncc_14)
                except: crt = 0

                # get the cri of today
                cri = 2
                # the GREEN potential
                if crp <= cfg.S_GREEN_CRP_CUT_VALUE_1: cri = 1
                if crt <= cfg.S_GREEN_RW_CUT_VALUE_2 and crp <= cfg.S_GREEN_CRP_CUT_VALUE_2: cri = 1

                # the RED potential
                if crt > cfg.S_RED_RW_CUT_VALUE_1 and crp > cfg.S_RED_CRP_CUT_VALUE_1: cri = 3
                if crp > cfg.S_RED_CRP_CUT_VALUE_2: cri = 3

                # get the crv of today
                crv = 0
                if i >= 7 + 7:
                    for j in range(1, 7+1):
                        crv += cris[i-7-j]
                
                # get the crc based on crv
                crc = 'Y'
                if crv <= 7: crc = 'G'
                if crv >=21: crc = 'R'

                # get the PVI as median value of this state
                try: pvi = df_cdcpvi_state.loc[date_val, 'pvi'].median()
                except: pvi = 0

                # get the FVP
                try:
                    fvc = df_actnow_state.loc[date_val, 'actuals.vaccinationsCompleted']
                    if pd.isna(fvc):
                        fvc = 0
                        fvp = 0
                    else:
                        fvp = fvc / pop
                except:
                    fvc = 0
                    fvp = 0

                # get the VAP and VAC
                try:
                    vac = df_actnow_state.loc[date_val, 'actuals.vaccinationsInitiated']
                    vap = df_actnow_state.loc[date_val, 'metrics.vaccinationsInitiatedRatio']
                
                    if pd.isna(vac):
                        vac = 0
                    if pd.isna(vap):
                        vap = 0
                except:
                    vac = 0
                    vap = 0

                # try the cdc vac data to update the ActNow data last date
                if i == (len(date_vals) - 1):
                    try:
                        # before 2021-03-08, use Administered_Dose2
                        # fvc2 = df_cdcvac_state.loc[date_val, 'Administered_Dose2']

                        # 2021-03-18: CDC updated the data source, use Series_Complete_Yes
                        fvc2 = df_cdcvac_state.loc[date_val, 'Series_Complete_Yes']
                        
                        if fvc2 > fvc:
                            fvc = fvc2
                            fvp = fvc2 / pop
                        else:
                            pass
                    except:
                        pass
                else:
                    pass

            else:
                # which means the no data? so, everything is 0
                ncc = 0
                dnc = 0
                d7v = 0
                npp = 0
                dpp = 0
                d7p = 0

                dth = 0
                dtr = 0

                tpr = 0
                ttr = 0
                tpt = 0
                t7r = 0

                cdt = cfg.CDT_CUT_VALUE

                crp = 0
                crt = 0
                cri = 0
                crv = 0
                crc = 'G'

                pvi = 0
                fvc = 0
                fvp = 0
                vac = 0
                vap = 0

            # fix values
            ncc = _floor(ncc)
            dnc = _floor(dnc)
            d7v = _floor(d7v)
            npp = _round(npp, 2)
            dpp = _round(dpp, 2)
            d7p = _round(d7p, 2)

            dth = _floor(dth)
            dtr = _round(dtr, 4)

            tpr = _round(tpr, 4)
            ttr = _floor(ttr)
            tpt = _floor(tpt)
            t7r = _round(t7r, 4)

            cdt = _round(cdt, 2)

            crp = _round(crp, 2)
            crt = _round(crt, 4)
            crc = crc

            pvi = _round(pvi, 4)

            fvc = _floor(fvc)
            fvp = _round(fvp, 4)
            vac = _floor(vac)
            vap = _round(vap, 4)
            
            # append values
            nccs.append(ncc)
            dncs.append(dnc)
            d7vs.append(d7v)
            npps.append(npp)
            dpps.append(dpp)
            d7ps.append(d7p)

            dths.append(dth)
            dtrs.append(dtr)

            ttrs.append(ttr)
            tpts.append(tpt)
            tprs.append(tpr)
            t7rs.append(t7r)
            
            cdts.append(cdt)

            crps.append(crp)
            crts.append(crt)
            cris.append(cri)
            crvs.append(crv)
            crcs.append(crc)

            pvis.append(pvi)

            fvcs.append(fvc)
            fvps.append(fvp)
            vacs.append(vac)
            vaps.append(vap)

            dates.append(date_val)

        # create JSON for this state
        j_state = {
            'state': state,
            'FIPS': FIPS,
            'pop': pop,
            'name': name,
            'date': parse_date,
            'lat': lat,
            'lon': lon,

            'nccs': nccs,
            'dncs': dncs,
            'd7vs': d7vs,

            'npps': npps,
            'dpps': dpps,
            'd7ps': d7ps,

            'tprs': tprs,
            'ttrs': ttrs,
            'tpts': tpts,
            't7rs': t7rs,

            'dths': dths,
            'dtrs': dtrs,

            'cdts': cdts,

            'crps': crps,
            'crts': crts,
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'pvis': pvis,

            'fvcs': fvcs,
            'fvps': fvps,
            'vacs': vacs,
            'vaps': vaps,

            'dates': dates
        }

        # save this json
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'USA-%s.json' % state
        )
        with open(fn, 'w') as fp:
            json.dump(j_state, fp, cls=NpEncoder)

    print('* done parsing the state data from JHU data %s' % (parse_date))


def parse_country_with_jhu_data_v2(parse_date=None):
    '''
    Parse world data

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
        - cdts: case doubling time
        - crcs: GYR CrRW status
        - crps: same as d7ps
        - crts: the ratio d7ps compared to last week
        - dates: dates of the data
    And the characteristics
        - state: the 3-digits abbreviation
        - FIPS: the 3-digits abbreviation
        - pop:
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
    # Parse JHU %s to generate world-level results
    ###############################################################
    """ % (parse_date))

    # create the dates for parsing
    date_vals = []
    date_cols = []
    # +7 for the 7 day average calculation
    dates = pd.date_range(cfg.FIRST_DATE, parse_date)
    for i in range(len(dates)):
        day = dates[i]
        date_vals.append(day.strftime('%Y-%m-%d'))
        date_cols.append(day.strftime('%-m/%-d/%y'))

    # get the world covid data
    fn_jhu_covid_data = cfg.FN_SAVE_JHU_WORLD_TS_COVID_DATA % parse_date
    fn_jhu_death_data = cfg.FN_SAVE_JHU_WORLD_TS_DEATH_DATA % parse_date

    # load data
    df_jhu_covid = pd.read_csv(fn_jhu_covid_data)
    df_jhu_death = pd.read_csv(fn_jhu_death_data)

    countries = df_jhu_covid['Country/Region'].unique().tolist()

    # sum as country
    df_jhu_covid = df_jhu_covid.groupby(['Country/Region']).sum()
    df_jhu_death = df_jhu_death.groupby(['Country/Region']).sum()

    df_jhu_covid.reset_index(inplace=True)
    df_jhu_death.reset_index(inplace=True)

    df_jhu_covid.set_index('Country/Region', inplace=True)
    df_jhu_death.set_index('Country/Region', inplace=True)

    print('* loaded world data %s lines' % len(df_jhu_covid))

    # load pop
    df_pop = pd.read_csv(cfg.FN_WORLD_POPU)
    df_pop.set_index('Name', inplace=True)

    # begin loop on countries
    for country in tqdm(countries):
        name = country

        if country not in df_pop.index:
            print('* NOT found %s' % name)
            continue

        FIPS = df_pop.loc[name, 'Code']
        pop = df_pop.loc[name, 'POP']
            
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

        dates = []

        for i in range(7, len(date_vals)):
            date_val = date_vals[i]
            date_col = date_cols[i]

            # get the basic values
            ncc = df_jhu_covid.loc[country, date_col]
            dnc = ncc - df_jhu_covid.loc[country, date_cols[i-1]]
            d7v = (ncc - df_jhu_covid.loc[country, date_cols[i-7]]) / 7
            npp = ncc / pop * cfg.N_PERCAPITA
            dpp = dnc / pop * cfg.N_PERCAPITA
            d7p = d7v / pop * cfg.N_PERCAPITA

            # get the death rate
            dth = df_jhu_death.loc[country, date_col]
            try: dtr = dth / ncc
            except: dtr = 0

            # get the CDT
            _ncc_past = df_jhu_covid.loc[country, date_cols[i-cfg.N_CDT_SMOOTH_DAYS]]
            cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)

            # get the crrw ratio
            crp = d7p
            _ncc_7 = df_jhu_covid.loc[country, date_cols[i-7]]
            # get the past ncc
            try: _ncc_14 = df_jhu_covid.loc[country, date_cols[i-14]]
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
            if i >= 7 + 7:
                for j in range(1, 7+1):
                    crv += cris[i - 7 - j]

            # get the crc based on crv
            crc = 'Y'
            if crv <= 7: crc = 'G'
            if crv >=21: crc = 'R'

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

            dates.append(date_val)

        # create JSON for this country
        j_country = {
            'state': FIPS,
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
            # 'cris': cris,
            # 'crvs': crvs,
            'crcs': crcs,

            'dates': dates
        }
            
        # save this country
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'WORLD-%s.json' % FIPS
        )
        with open(fn, 'w') as fp:
            json.dump(j_country, fp, cls=NpEncoder)

    return 0



if __name__ == "__main__":
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    parse_date = yesterday.strftime('%Y-%m-%d')

    # create arguments parser
    parser = argparse.ArgumentParser(description='Parse the data files to generate county/state/US level results')
    parser.add_argument("--lv", type=str,
        choices=['county', 'state', 'country', 'mchrr', 'all'], default='all',
        help="Which level of data to parse? county, state, mchrr, country, or all?")
    parser.add_argument("--ds", type=str,
        choices=[
            'cdcpvi', 'usafacts', 'jhu',
            'covidtracking', 
            'actnow', 'nytimes', 
            'owidvac'
        ], default='cdcpvi',
        help="Specify the main data source for USA county")
    parser.add_argument("--date", type=str, 
        help="Specify the date (YYYY-MM-DD) to parse, empty is %s" % parse_date)

    # parse the input parameter
    args = parser.parse_args()

    if args.date is not None:
        parse_date = args.date
    
    if args.lv == 'all' or 'county' in args.lv:
        if args.ds == 'usafacts':
            parse_county_with_usafacts_and_cdcpvi_data_v2(parse_date)
        elif args.ds == 'cdcpvi':
            parse_county_with_actnow_and_cdcpvi_data_v2(parse_date)
        elif args.ds == 'jhu':
            parse_county_with_jhu_and_cdcpvi_data_v2(parse_date)
        elif args.ds == 'actnow':
            parse_county_with_actnow_and_cdcpvi_data_v2(parse_date)
        else:
            parse_county_with_actnow_and_cdcpvi_data_v2(parse_date)

    if args.lv == 'all' or 'state' in args.lv:
        if args.ds == 'actnow':
            parse_state_with_cdcpvi_and_actnow_v2(parse_date)
        elif args.ds == 'jhu':
            parse_state_with_jhu_and_cdcpvi_and_actnow_v2(parse_date)
        elif args.ds == 'covidtracking':
            parse_state_with_covidtracking_and_cdcpvi_and_jhucci_data_and_cdcvac_v2(parse_date)
        else:
            parse_state_with_cdcpvi_and_actnow_v2(parse_date)

    if args.lv == 'all' or 'country' in args.lv:
        if args.ds == 'owidvac':
            parse_country_with_jhu_and_owid_data_v2(parse_date)
        elif args.ds == 'jhu':
            parse_country_with_jhu_data_v2(parse_date)
        else:
            parse_country_with_jhu_and_owid_data_v2(parse_date)

    if args.lv == 'all' or 'mchrr' in args.lv:
        parse_mchrr_with_actnow_and_cdcpvi_data_v2(parse_date)