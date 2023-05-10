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

import ds_util
from ds_util import NpEncoder
from ds_util import _floor
from ds_util import _round


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

    
def parse_county_with_actnow_and_cdcpvi_data_v2(parse_date=None):
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
    #########################################################################
    # Parse CDCPVI+ACTNOW data %s to generate county-level results
    #########################################################################
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

    # get the actnow data
    fn_actnow_data = cfg.FN_SAVE_ACTNOW_COUNTY_DATA % parse_date
    df_actnow = pd.read_csv(fn_actnow_data)

    # get all the counties from actnow
    counties = df_actnow['fips'].unique().tolist()
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

    # begin loop on each county for debugging purpose
    # because it takes very long time to run ...
    # for countyFIPS in tqdm(counties):
    #     df_cdcpvi_county = df_cdcpvi[df_cdcpvi['countyFIPS']==countyFIPS].copy()
    #     df_actnow_county = df_actnow[df_actnow['fips'] == countyFIPS].copy()

    #     __parse_county_with_actnow_and_cdcpvi_data_v2(
    #         df_actnow_county, 
    #         df_cdcpvi_county, 
    #         df_geo, 
    #         df_pop, 
    #         date_vals, 
    #         countyFIPS
    #     )



    # begin the multiprocessing
    with multiprocessing.Pool() as pool:
        arguments_list = [ ]
        print('* creating arguments list for mapping')
        for _fips in counties:
            df_cdcpvi_county = df_cdcpvi[df_cdcpvi['countyFIPS']==_fips].copy()
            df_actnow_county = df_actnow[df_actnow['fips'] == _fips].copy()

            arguments_list.append((
                df_actnow_county, 
                df_cdcpvi_county, 
                df_geo, 
                df_pop, 
                date_vals, 
                _fips
            ))

        print('* run multiprocessing to parse the counties')
        for _ in tqdm(pool.istarmap( \
            func=__parse_county_with_actnow_and_cdcpvi_data_v2, \
            iterable=arguments_list \
            ), total=len(counties)):
            pass
    

    # for result in tqdm(pool.imap_unordered(func=func, iterable=argument_list), total=len(argument_list)):
    #     result_list_tqdm.append(result)

    print('* done parsing all the county data %s from CDC PVI and COVID Act Now' % (parse_date))


def __parse_county_with_actnow_and_cdcpvi_data_v2(
    df_actnow_county, 
    df_cdcpvi_county, 
    df_geo, 
    df_pop, 
    date_vals, 
    countyFIPS):
    '''
    Mainly based COVID ACT Now Data
    '''
    parse_date = date_vals[-1]

    # there are missing in the actnow data, fill the missing
    missing_dates = []
    existing_dates = set(df_actnow_county.date.values)
    for date in date_vals:
        if date not in existing_dates:
            # missing data is very common in actnow ...
            df_actnow_county = df_actnow_county.append(
                {'date': date}, 
                ignore_index=True
            )
            missing_dates.append(date)

    if len(missing_dates) > 0:
        print(f"* !!!! actnow county {countyFIPS} has {len(missing_dates)}/{len(date_vals)} missing dates but fixed!")

    df_actnow_county.sort_values(by=['date'], inplace=True)
    df_actnow_county.set_index('date', inplace=True)
    df_actnow_county.fillna(method="ffill", inplace=True)
    df_actnow_county.fillna(0, inplace=True)

    # there are missing in the cdcpvi data, fill the missing
    missing_dates = []
    existing_dates = set(df_cdcpvi_county.date.values)
    for date in date_vals:
        if date not in existing_dates:
            # missing data is very common in actnow ...
            df_cdcpvi_county = df_cdcpvi_county.append(
                {'date': date}, 
                ignore_index=True
            )
            missing_dates.append(date)

    if len(missing_dates) > 0:
        print(f"* !!!! cdcpvi county {countyFIPS} has {len(missing_dates)}/{len(date_vals)} missing dates but fixed!")

    # set index for data
    df_cdcpvi_county.set_index('date', inplace=True)

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
    
    # for all date, get the values, start from 14 day for calculating the CrRW
    for i in range(cfg.START_DATE_IDX, len(date_vals)):
        date_val = date_vals[i]

        # get the basics
        ncc = df_actnow_county.loc[date_val, 'actuals.cases']
        dnc = ncc - df_actnow_county.loc[date_vals[i-1], 'actuals.cases']
        d7v = (ncc - df_actnow_county.loc[date_vals[i-7], 'actuals.cases']) / 7
        npp = ncc / pop * cfg.N_PERCAPITA
        dpp = dnc / pop * cfg.N_PERCAPITA
        d7p = d7v / pop * cfg.N_PERCAPITA

        # get the Death rate
        dth = df_actnow_county.loc[date_val, 'actuals.deaths']
        # try: dtr = dth / ncc
        # except: dtr = 0
        # to avoid divide by zero exception
        if ncc == 0: dtr = 0
        else: dtr = dth / ncc

        # get the CDT
        _ncc_past = df_actnow_county.loc[date_vals[i-cfg.N_CDT_SMOOTH_DAYS], 'actuals.cases']
        # cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)
        # to avoid divide by zero exception
        if _ncc_past == 0: cdt = 0
        else: cdt = cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / _ncc_past)


        # get the crrw ratio
        crp = d7p
        _ncc_7 = df_actnow_county.loc[date_vals[i-7], 'actuals.cases']
        # get the past ncc
        try: _ncc_14 = df_actnow_county.loc[date_vals[i-14], 'actuals.cases']
        except: _ncc_14 = 0

        # get the crt
        # try: crt = (ncc - _ncc_7) / (_ncc_7 - _ncc_14)
        # except: crt = 0
        # to avoid divide by zero exception
        if (_ncc_7 - _ncc_14) == 0: crt = 0
        else: crt = (ncc - _ncc_7) / (_ncc_7 - _ncc_14)
    
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
