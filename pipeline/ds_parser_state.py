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


def parse_state_with_jhu_and_cdcpvi_and_actnow_v2(parse_date=None):
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
        df_jhu_state = df_jhu[df_jhu['state']==state].copy()
        df_jhu_state.set_index('date', inplace=True)

        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS].copy()
        df_cdcpvi_state.set_index('date', inplace=True)

        df_actnow_state = df_actnow[df_actnow['state']==state].copy()
        df_actnow_state.set_index('date', inplace=True)
        
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


def parse_state_with_cdcpvi_and_actnow_v2(parse_date=None):
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
    # Parse CDCPVI_ACTNOW Data %s to generate state-level results
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

    # get the vaccination data
    fn_actnow = cfg.FN_SAVE_ACTNOW_STATE_DATA % parse_date
    df_actnow = pd.read_csv(fn_actnow)

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
        print("* parsing state [%s, %s/%s]" % (state, name, FIPS))

        df_cdcpvi_state = df_cdcpvi[df_cdcpvi['stateFIPS']==stateFIPS].copy()
        df_cdcpvi_state.set_index('date', inplace=True)

        df_actnow_state = df_actnow[df_actnow['state']==state].copy()
        print(df_actnow_state.tail(10))

        # there are missing in the actnow data, fill the missing
        missing_dates = []
        existing_dates = set(df_actnow_state.date.values)
        for date in date_vals:
            if date not in existing_dates:
                # missing data is very common in actnow ...
                df_actnow_state = df_actnow_state.append(
                    {'date': date}, 
                    ignore_index=True
                )
                missing_dates.append(date)

        if len(missing_dates) > 0:
            print(f"* !!!! actnow state {state} has {len(missing_dates)}/{len(date_vals)} missing dates but fixed!")

        # set index
        df_actnow_state.set_index('date', inplace=True)
        print('* get df_actnow_stat as:')

        # fix the missing values for tests and others.
        df_actnow_state.fillna(method="ffill", inplace=True)
        
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

                ttr = df_actnow_state.loc[date_val, 'actuals.positiveTests'] + \
                      df_actnow_state.loc[date_val, 'actuals.negativeTests']

                tpt = df_actnow_state.loc[date_val, 'actuals.positiveTests']
                tpr = 0 if ttr == 0 else tpt / ttr
                dth = df_actnow_state.loc[date_val, 'actuals.deaths']
                dtr = 0 if ncc == 0 else dth / ncc

                _ttr7 = df_actnow_state.loc[date_vals[i-7], 'actuals.positiveTests'] + \
                        df_actnow_state.loc[date_vals[i-7], 'actuals.negativeTests']
                _tpt7 = df_actnow_state.loc[date_vals[i-7], 'actuals.positiveTests']
                t7r = 0 if (ttr - _ttr7) == 0 else (tpt - _tpt7) / (ttr - _ttr7)

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
                if crt <= cfg.S_GREEN_RW_CUT_VALUE_2 and crp <= cfg.S_GREEN_CRP_CUT_VALUE_2: cri = 1

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

