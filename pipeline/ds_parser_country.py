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


def parse_country_with_jhu_and_owid_data_v2(parse_date=None):
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
        - fvcs: Fully Vaccinated Count
        - fvps: Fully Vaccinated Percentage
        - vacs: Total number of doses administered
        - vaps: Total percentage of doses administered
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
    fn_owidvac_vac_data = cfg.FN_SAVE_OWIDVAC_WORLD_VAC_DATA % parse_date

    # load data
    df_jhu_covid = pd.read_csv(fn_jhu_covid_data)
    df_jhu_death = pd.read_csv(fn_jhu_death_data)

    countries = df_jhu_covid['Country/Region'].unique().tolist()

    # load the owid data
    df_owid_vac = pd.read_csv(fn_owidvac_vac_data)

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

        # split a regional df and use date as index
        df_owid_vac_country = df_owid_vac[df_owid_vac['iso_code'] == FIPS].copy()
        df_owid_vac_country.sort_values(by=['date'], inplace=True)
        df_owid_vac_country.set_index('date', inplace=True)

        # fill the na values with available non-na value
        df_owid_vac_country.fillna(method='ffill', inplace=True)

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

        fvcs = []
        fvps = []

        vacs = []
        vaps = []

        dates = []

        for i in range(cfg.START_DATE_IDX, len(date_vals)):
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
            if i >= 7 + cfg.START_DATE_IDX:
                for j in range(1, 7+1):
                    crv += cris[i - cfg.START_DATE_IDX - j]

            # get the crc based on crv
            crc = 'Y'
            if crv <= 7: crc = 'G'
            if crv >=21: crc = 'R'

            # get the vaccination data
            try: fvc = df_owid_vac_country.loc[date_val, 'people_fully_vaccinated']
            except: fvc = 0
            fvp = fvc / pop

            try: vac = df_owid_vac_country.loc[date_val, 'total_vaccinations']
            except: vac = 0
            vap = vac / pop

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

            fvcs.append(fvc)
            fvps.append(fvp)
            vacs.append(vac)
            vaps.append(vap)

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

            'fvcs': fvcs,
            'fvps': fvps,
            'vacs': vacs,
            'vaps': vaps,

            'dates': dates
        }
            
        # save this country
        fn = os.path.join(
            cfg.FOLDER_PRS, cfg.FOLDER_V2, parse_date, 'WORLD-%s.json' % FIPS
        )
        with open(fn, 'w') as fp:
            json.dump(j_country, fp, cls=NpEncoder)

    return 0
