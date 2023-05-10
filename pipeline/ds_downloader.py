#!/usr/bin/env python3

# Copyright (c) Huan He (He.Huan@mayo.edu)
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

#%% load packages
import os
import json
import shutil
import pathlib
from urllib import parse

import dateutil
import datetime
from datetime import timedelta
import argparse

import pandas as pd
from tqdm import tqdm
import requests

import wget

from timeloop import Timeloop

import ds_config as cfg

import logging
logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger("Downloader")
logger.setLevel(logging.INFO)


print('* loaded packages!')

#%% define the functions

def _int(v):
    '''
    convert a value to integer
    '''
    try:
        return int(v)
    except:
        return 0

def download_county_data_from_usafact(parse_date=None):
    '''
    Download COVID-19 case data and death data from USAFacts
    '''
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
    # Download County-level Data from 
    # %s
    # %s
    ###############################################################
    """ % (cfg.DS_USAFACTS_CONFIRM, cfg.DS_USAFACTS_DEATH))
    covid_data = pd.read_csv(cfg.DS_USAFACTS_CONFIRM)
    print('* loaded USAFACT covid confirmed data')

    death_data = pd.read_csv(cfg.DS_USAFACTS_DEATH)
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

    # check the death data
    cols_rm = []
    for col in death_data.columns:
        if col.startswith('Unnamed'):
            cols_rm.append(col)
    if len(cols_rm) > 0:
        death_data.drop(columns=cols_rm, inplace=True)
        print('* removed error name columns in death_data: %s' % cols_rm)
    else:
        print('* no error name columns in death_data')

    # rename column to mm/dd/yy format
    # how can they change header date format sometimes!?
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

    # set index
    covid_data.set_index('countyFIPS', inplace=True)
    death_data.set_index('countyFIPS', inplace=True)

    # remove the fips==0 lines since no county info related
    covid_data = covid_data.loc[covid_data.index>0, :]
    death_data = death_data.loc[death_data.index>0, :]

    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_USAFACTS):
        os.makedirs(cfg.FOLDER_SRC_USAFACTS, exist_ok=True)

    # save covid data
    # then last column should be the date
    last_col = covid_data.columns[-1]
    dt = dateutil.parser.parse(last_col)
    last_date = dt.strftime('%Y-%m-%d')
    fn_date = last_date if parse_date is None else parse_date
    fn = cfg.FN_SAVE_USAFACTS_COUNTY_COVID_DATA % fn_date
    covid_data.to_csv(fn)
    print("* saved %s county covid_data to %s" % (last_date, fn))

    # save death data
    # sometimes the last date column of death data is not as same as covid data
    last_col = death_data.columns[-1]
    dt = dateutil.parser.parse(last_col)
    last_date = dt.strftime('%Y-%m-%d')
    fn_date = last_date if parse_date is None else parse_date
    fn = cfg.FN_SAVE_USAFACTS_COUNTY_DEATH_DATA % fn_date
    death_data.to_csv(fn)
    print("* saved %s county death_data to %s" % (last_date, fn))

    return fn_date


def download_state_data_from_covidtracking(parse_date=None):
    '''
    Download the COVID-19 state level data from COVID Tracking Project
    '''
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
    # Download State-level Data from %s
    ###############################################################
    """ % cfg.DS_COVIDTRACKING_STATE)
    state_data = pd.read_csv(cfg.DS_COVIDTRACKING_STATE)

    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_COVIDTRACKING):
        os.makedirs(cfg.FOLDER_SRC_COVIDTRACKING, exist_ok=True)

    # save data file
    last_date = state_data.date.max()
    fn_date = last_date if parse_date is None else parse_date
    fn = cfg.FN_SAVE_COVIDTRACKING_STATE_DATA % fn_date
    state_data.to_csv(fn, index=False)
    print("* saved %s state data to %s" % (last_date, fn))

    return fn_date


def download_usa_data_from_covidtracking(parse_date=None):
    '''
    Download the COVID-19 usa level data from COVID-19 Tracking Project
    '''
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
    # Download USA-level Data from %s
    ###############################################################
    """ % cfg.DS_COVIDTRACKING_USA)
    usa_data = pd.read_csv(cfg.DS_COVIDTRACKING_USA)

    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_COVIDTRACKING):
        os.makedirs(cfg.FOLDER_SRC_COVIDTRACKING)

    # save data file
    last_date = usa_data.date.max()
    fn_date = last_date if parse_date is None else parse_date
    fn = cfg.FN_SAVE_COVIDTRACKING_USA_DATA % fn_date
    usa_data.to_csv(fn, index=False)
    print("* saved %s usa data to %s" % (last_date, fn))

    return fn_date


def _download_state_raw_data_from_jhu(parse_date=None):
    '''
    Download the state level raw data from JHU
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
        date_for_src = yesterday.strftime('%m-%d-%Y')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
        date_for_src = yesterday.strftime('%m-%d-%Y')

    print("""
    ###############################################################
    # Download %s state raw data from JHU
    ###############################################################
    """ % dt)

    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_JHU_RAW):
        os.makedirs(cfg.FOLDER_SRC_JHU_RAW, exist_ok=True)

    # generate the URL for downloading the raw
    url_raw = cfg.DS_JHU_STATE_DAILY % date_for_src

    # create the fn for save
    save_raw_fn = cfg.FN_SAVE_JHU_STATE_RAW_DATA % dt

    # check if exists
    if os.path.exists(save_raw_fn):
        os.remove(save_raw_fn)
        print('* removed %s data exists %s' % (dt, save_raw_fn))

    # else:
    #     wget.download(url_raw, save_raw_fn)
    #     print('* done downloading %s to %s' % (dt, save_raw_fn))

    # 2021-04-25: no need to check, just download
    wget.download(url_raw, save_raw_fn)
    print('* done downloading %s to %s' % (dt, save_raw_fn))

    return dt


def download_state_data_from_jhu(parse_date=None):
    '''
    Get the state data from JHU and merge
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
        parse_date = dt
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
    
    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_JHU):
        os.makedirs(cfg.FOLDER_SRC_JHU, exist_ok=True)

    # download the raw data
    _ = _download_state_raw_data_from_jhu(parse_date)

    # merge to produce the data file
    dates = pd.date_range(cfg.FIRST_DATE_JHU, parse_date)

    # fips2abbr
    df_geo = pd.read_csv(cfg.FN_STATE_GEO)
    f2a_dict = dict(zip(df_geo.stateFIPS.tolist(), df_geo.stateAbbr.tolist()))
    f2a_dict[0]     = 'XX' # ???
    f2a_dict[888]   = 'DP' # Diamon Princess
    f2a_dict[88888] = 'DP' # Diamon Princess
    f2a_dict[999]   = 'GP' # Grand Princess
    f2a_dict[99999] = 'GP' # Grand Princess

    dfs = []
    for date in tqdm(dates):
        dt = date.strftime("%Y-%m-%d")
        # check if the data file exists
        raw_fn = cfg.FN_SAVE_JHU_STATE_RAW_DATA % dt

        if os.path.exists(raw_fn):
            # if both exist, OK
            pass
        else:
            # if not exist, need to download from data source
            _download_state_raw_data_from_jhu(dt)
        
        # get the data
        df_raw = pd.read_csv(raw_fn)

        # get the selected columns since other columns are not required
        if 'Total_Test_Results' not in df_raw.columns:
            # the old data may not have this column
            df_raw['Total_Test_Results'] = None

        dft = df_raw[['FIPS', 'Confirmed', 'Deaths', 'Recovered', 'Total_Test_Results']]
        dft['state'] = dft['FIPS'].apply(lambda v: f2a_dict[_int(v)])

        # rename the columns to make it easier for parsing in the next stage
        dft.rename(columns={
            'Confirmed': 'cases',
            'Deaths': 'deaths',
            'Recovered': 'recovered',
            'Total_Test_Results': 'totalTestResults'
        }, inplace=True)

        # add a date column
        dft['date'] = dt

        # make sure the data types
        dft['FIPS'] = dft['FIPS'].apply(lambda v: _int(v))
        dft['cases'] = dft['cases'].apply(lambda v: _int(v))
        dft['deaths'] = dft['deaths'].apply(lambda v: _int(v))
        dft['recovered'] = dft['recovered'].apply(lambda v: _int(v))
        dft['totalTestResults'] = dft['totalTestResults'].apply(lambda v: _int(v))

        # put this data into 
        dfs.append(dft)
    
    df_all = pd.concat(dfs, ignore_index=True)
    full_save_all_fn = cfg.FN_SAVE_JHU_STATE_ALL_DATA % parse_date
    df_all.to_csv(full_save_all_fn, index=False)
    print('* merged %s state data to %s' % (parse_date, full_save_all_fn))

    return parse_date


def download_world_ts_data_from_jhu(parse_date=None):
    '''
    Download the world data from JHU repo
    '''
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)
        print('* got parse_date=%s from input' % parse_date)
    
    if not os.path.exists(cfg.FOLDER_SRC_JHU):
        os.makedirs(cfg.FOLDER_SRC_JHU, exist_ok=True)

    url_covid = cfg.DS_JHU_WORLD_TS_CONFIRMED
    fn_covid = cfg.FN_SAVE_JHU_WORLD_TS_COVID_DATA % parse_date

    # # check if exists
    if os.path.exists(fn_covid):
        os.remove(fn_covid)
        print('* removed %s data exists %s' % (parse_date, fn_covid))
    # else:
    #     wget.download(url_covid, fn_covid)
    #     print('* done downloading %s to %s' % (parse_date, fn_covid))

    # 2021-04-25: just download directly
    wget.download(url_covid, fn_covid)
    print('* done downloading %s to %s' % (parse_date, fn_covid))

    url_death = cfg.DS_JHU_WORLD_TS_DEATH
    fn_death = cfg.FN_SAVE_JHU_WORLD_TS_DEATH_DATA % parse_date

    # check if exists
    if os.path.exists(fn_death):
        os.remove(fn_death)
        print('* removed %s data exists %s' % (parse_date, fn_death))
    # else:
    #     wget.download(url_death, fn_death)
    #     print('* done downloading %s to %s' % (parse_date, fn_death))

    # 2021-04-25: just download directly
    wget.download(url_death, fn_death)
    print('* done downloading %s to %s' % (parse_date, fn_death))

    return parse_date


def _download_allusa_raw_and_rst_data_from_cdcpvi(parse_date=None):
    '''
    Get the raw data from CDC
    '''
    if parse_date == None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        date_for_src = yesterday.strftime('%Y%m%d')
        parse_date = yesterday.strftime('%Y-%m-%d')
    else:
        # the date in the fn is tomorrow of parse_date
        date = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        date_for_src = date.strftime('%Y%m%d')

    print("""
    ###############################################################
    # Download %s All USA raw data from CDCPVI
    ###############################################################
    """ % parse_date)
    
    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_CDCPVI_RAW):
        os.makedirs(cfg.FOLDER_SRC_CDCPVI_RAW, exist_ok=True)

    # generate the URL for downloading the raw
    url_raw = cfg.DS_CDCPVI_RAW_DATA % date_for_src

    # create the fn for save
    save_raw_fn = cfg.FN_SAVE_CDCPVI_USA_RAW_DATA % parse_date

    # check if exists
    if os.path.exists(save_raw_fn):
        os.remove(save_raw_fn)
        print('* removed %s data exists %s' % (parse_date, save_raw_fn))
    
    wget.download(url_raw, save_raw_fn)
    print('* done downloading %s to %s' % (parse_date, save_raw_fn))

    # generate the URL for downloading raw pvi
    url_rst = cfg.DS_CDCPVI_RST_DATA % date_for_src

    # create the fn for save
    save_rst_fn = cfg.FN_SAVE_CDCPVI_USA_RST_DATA % parse_date

    # check if exists
    if os.path.exists(save_rst_fn):
        # remove the existed file
        os.remove(save_rst_fn)
        print('* removed %s data %s' % (parse_date, save_rst_fn))
    # else:
    #     wget.download(url_rst, save_rst_fn)
    #     print('* done downloading %s to %s' % (parse_date, save_rst_fn))

    # 2021-04-25: just download
    wget.download(url_rst, save_rst_fn)
    print('* done downloading %s to %s' % (parse_date, save_rst_fn))

    return parse_date


def download_allusa_data_from_cdcpvi(parse_date=None):
    '''
    Get the data from CDC PVI
    '''
    if parse_date == None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')
    
    print("""
    ###############################################################
    # Download All USA data from CDCPVI
    ###############################################################
    """)
    
    # before saving, make sure the foler exsits
    if not os.path.exists(cfg.FOLDER_SRC_CDCPVI):
        os.makedirs(cfg.FOLDER_SRC_CDCPVI, exist_ok=True)

    # download the raw data
    _ = _download_allusa_raw_and_rst_data_from_cdcpvi(parse_date)

    # merge to produce the data
    dates = pd.date_range(cfg.FIRST_DATE, parse_date)

    dfs = []
    for date in tqdm(dates):
        dt = date.strftime("%Y-%m-%d")
        # check if the data file exists
        raw_fn = cfg.FN_SAVE_CDCPVI_USA_RAW_DATA % dt
        rst_fn = cfg.FN_SAVE_CDCPVI_USA_RST_DATA % dt

        if os.path.exists(raw_fn) and os.path.exists(rst_fn):
            # if both exist, OK
            pass
        else:
            # if not exist, need to download from data source
            _download_allusa_raw_and_rst_data_from_cdcpvi(dt)
        
        # get the data
        df_raw = pd.read_csv(raw_fn, skiprows=12)
        df_rst = pd.read_csv(rst_fn)

        # get the selected columns since other columns are not required
        dft_raw = df_raw[['casrn', 'name', 'Cases', 'Deaths']]
        dft_rst = df_rst[['ToxPi Score', 'Name']]

        # merge!
        dft = pd.merge(dft_raw, dft_rst, how='inner', 
                left_on="name", right_on='Name')

        # rename the columns to make it easier for parsing in the next stage
        dft.rename(columns={
            'casrn': 'countyFIPS',
            'ToxPi Score': 'pvi',
            'Cases': 'cases',
            'Deaths': 'deaths',
        }, inplace=True)

        # remove the name, just need the fips
        del dft['name']
        del dft['Name']

        # add a date column
        dft['date'] = dt

        # reduce the digits in pvi
        dft['pvi'] = dft['pvi'].round(4)

        # put this data into 
        dfs.append(dft)
    
    df_all = pd.concat(dfs, ignore_index=True)
    full_save_all_fn = cfg.FN_SAVE_CDCPVI_USA_ALL_DATA % parse_date
    df_all.to_csv(full_save_all_fn, index=False)
    print('* merged %s all usa data to %s' % (parse_date, full_save_all_fn))

    return parse_date


def download_state_vax_data_from_cdvvac(parse_date=None):
    '''

    '''
    return parse_date


def download_current_state_vac_data_from_cdvvac(parse_date=None):
    '''
    Download the current CDCVAC data 

    Due to the limitation of the data source, the history data is not available
    The parse data is just a reference
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')
        dt = parse_date
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date

    # load the latest data
    r = requests.get(cfg.DS_CDCVAC_STATE)
    j = r.json()
    dt_data = j['vaccination_data'][0]['Date']

    # save the JSON file
    if not os.path.exists(cfg.FOLDER_SRC_CDCVAC_RAW):
        os.makedirs(cfg.FOLDER_SRC_CDCVAC_RAW, exist_ok=True)

    fn = cfg.FN_SAVE_CDCVAC_STATE_VAC_RAW_DATA % dt_data
    json.dump(j, open(fn, 'w'))
    print('* saved CDC Vaccination raw data %s to %s' % (dt_data, fn))

    # convert to csv
    # try to create a history file
    dts = pd.date_range(cfg.FIRST_DATE_VAC, dt_data)
    dfts = []
    for date in dts:
        # load the raw data
        date_str = date.strftime("%Y-%m-%d")
        fn_dt = cfg.FN_SAVE_CDCVAC_STATE_VAC_RAW_DATA % date_str
        try:
            tmp_j = json.load(open(fn_dt, 'r'))

            # make a tmp df
            dft = pd.DataFrame(tmp_j['vaccination_data'])
            cols_need_rename = {
                'Date': 'date'
            }
            dft.rename(columns=cols_need_rename, inplace=True)
            dfts.append(dft)
        except Exception as err:
            print('* skip %s cdc vac data when merging error %s' % (
                date_str, err
            ))

    # merge as 
    df = pd.concat(dfts)
    # need to save the file as the date of the data
    fn = cfg.FN_SAVE_CDCVAC_STATE_VAC_DATA % dt_data
    df.to_csv(fn, index=False)
    print('* saved CDC Vaccination csv data %s to %s' % (dt_data, fn))

    return dt_data


def download_usa_vax_data_from_jhucci(parse_date=None):
    '''
    Download the vaccine data
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')
        dt = parse_date
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date

    try:
        df = pd.read_csv(cfg.DS_JHUCCI_VAX_USA)

        # convert date format
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].apply(lambda v: v.strftime('%Y-%m-%d'))
    
    # save the JSON file
        if not os.path.exists(cfg.FOLDER_SRC_JHUCCI_VAX):
            os.makedirs(cfg.FOLDER_SRC_JHUCCI_VAX, exist_ok=True)
            
        full_fn = cfg.FN_SAVE_JHUCCI_STATE_VAX_DATA % dt
        df.to_csv(full_fn, index=False)
        print('* saved %s jhucci vax data to %s' % (parse_date, full_fn))

        return parse_date
    
    except:
        return None


def download_world_vax_data_from_owidvac(parse_date=None):
    '''
    Download the vaccine data from our world in data
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')
        dt = parse_date
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date

    try:
        df = pd.read_csv(cfg.DS_OWIDVAC_WORLD)

        # fill the missing dates for each country
        countries = df.iso_code.unique().tolist()
        date_vals = df.date.unique().tolist()
        date_vals.sort()
        
        cnt = 0
        print('* fixing missing dates in country data ...')
        for country in tqdm(countries):
            for date_val in date_vals:
                is_date_data_available = df.loc[(df.iso_code == country) & (df.date == date_val), 'date'].count()

                if is_date_data_available == 0:
                    # which means no available 
                    df = df.append({'date': date_val, 'iso_code': country}, ignore_index=True)
                    cnt += 1
        
        # save the JSON file
        if not os.path.exists(cfg.FOLDER_SRC_OWIDVAC):
            os.makedirs(cfg.FOLDER_SRC_OWIDVAC, exist_ok=True)
            
        full_fn = cfg.FN_SAVE_OWIDVAC_WORLD_VAC_DATA % dt
        df.to_csv(full_fn, index=False)
        print('* saved %s owid vac data (added %s records) to %s' % (parse_date, cnt, full_fn))

        return parse_date
    
    except:
        return None


def download_state_data_from_actnow(parse_date=None):
    '''
    Download the COVID Act Now state-level data
    '''
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
    # Download State-level Data from %s
    ###############################################################
    """ % cfg.DS_ACTNOW_TS_STATE)
    df = pd.read_csv(cfg.DS_ACTNOW_TS_STATE)

    # since we download the parse_date
    # the data must be available for most of the regions
    states = df.state.unique().tolist()

    for state in tqdm(states):
        # need to fill the nan values for cases
        df.loc[df.state == state, 'actuals.cases'] = df.loc[df.state == state, 'actuals.cases'].fillna(method='ffill').fillna(0)
        # fill the nan values for deaths
        df.loc[df.state == state, 'actuals.deaths'] = df.loc[df.state == state, 'actuals.deaths'].fillna(method='ffill').fillna(0)
        # fill the nan values for vaccination
        df.loc[df.state == state, 'actuals.vaccinationsCompleted'] = df.loc[df.state == state, 'actuals.vaccinationsCompleted'].fillna(method='ffill').fillna(0)
    print('* fixed the missing for %s states' % (len(states)))

    # create the folder if not exist
    if not os.path.exists(cfg.FOLDER_SRC_ACTNOW):
        os.makedirs(cfg.FOLDER_SRC_ACTNOW, exist_ok=True)

    # save the data
    full_save_fn = cfg.FN_SAVE_ACTNOW_STATE_DATA % parse_date
    df.to_csv(full_save_fn, index=False)
    print('* saved %s COVID Act Now state data to %s' % (parse_date, full_save_fn))


def download_county_data_from_actnow(parse_date=None):
    '''
    Download the COVID Act Now county-level data
    '''
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
    # Download County-level Data from %s
    ###############################################################
    """ % cfg.DS_ACTNOW_TS_COUNTY)
    df = pd.read_csv(cfg.DS_ACTNOW_TS_COUNTY)

    # the raw county data is too large ... just keep the needed columns
    df = df[[
        'fips', 'state', 'date',
        'actuals.cases', 'actuals.deaths',
        'actuals.vaccinationsInitiated', 'actuals.vaccinationsCompleted',
    ]]

    # create the folder if not exist
    if not os.path.exists(cfg.FOLDER_SRC_ACTNOW):
        os.makedirs(cfg.FOLDER_SRC_ACTNOW, exist_ok=True)

    # save the data
    full_save_fn = cfg.FN_SAVE_ACTNOW_COUNTY_DATA % parse_date
    df.to_csv(full_save_fn, index=False)
    print('* saved %s COVID Act Now county data to %s' % (parse_date, full_save_fn))


def download_usa_data_from_nytimes(parse_date=None):
    '''
    Download the USA data from NYTimes data source
    '''
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
    # Download USA-level Data from %s
    ###############################################################
    """ % cfg.DS_NYTIMES_TS_USA)
    df = pd.read_csv(cfg.DS_NYTIMES_TS_USA)

    # since we download the parse_date
    # create the folder if not exist
    if not os.path.exists(cfg.FOLDER_SRC_NYTIMES):
        os.makedirs(cfg.FOLDER_SRC_NYTIMES, exist_ok=True)

    # save the data
    full_save_fn = cfg.FN_SAVE_NYTIMES_USA_DATA % parse_date
    df.to_csv(full_save_fn, index=False)
    print('* saved %s USA data to %s' % (parse_date, full_save_fn))


def download_state_data_from_nytimes(parse_date=None):
    '''
    Download the State data from NYTimes data source
    '''
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
    # Download State-level Data from %s
    ###############################################################
    """ % cfg.DS_NYTIMES_TS_STATE)
    df = pd.read_csv(cfg.DS_NYTIMES_TS_STATE)

    # since we download the parse_date
    # create the folder if not exist
    if not os.path.exists(cfg.FOLDER_SRC_NYTIMES):
        os.makedirs(cfg.FOLDER_SRC_NYTIMES, exist_ok=True)

    # save the data
    full_save_fn = cfg.FN_SAVE_NYTIMES_STATE_DATA % parse_date
    df.to_csv(full_save_fn, index=False)
    print('* saved %s state data to %s' % (parse_date, full_save_fn))


def download_county_data_from_nytimes(parse_date=None):
    '''
    Download the county data from NYTimes data source
    '''
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
    # Download County-level Data from %s
    ###############################################################
    """ % cfg.DS_NYTIMES_TS_COUNTY)
    df = pd.read_csv(cfg.DS_NYTIMES_TS_COUNTY)

    # since we download the parse_date
    # create the folder if not exist
    if not os.path.exists(cfg.FOLDER_SRC_NYTIMES):
        os.makedirs(cfg.FOLDER_SRC_NYTIMES, exist_ok=True)

    # save the data
    full_save_fn = cfg.FN_SAVE_NYTIMES_COUNTY_DATA % parse_date
    df.to_csv(full_save_fn, index=False)
    print('* saved %s county data to %s' % (parse_date, full_save_fn))


# the main loop obj
tl = Timeloop()
@tl.job(interval=timedelta(hours=1))
def run_download_current_state_vac_data_from_cdvvac():
    try:
        download_current_state_vac_data_from_cdvvac()
    except Exception as err:
        logger.info('* Err %s happens when download_current_state_vac' % err)
    

if __name__ == "__main__":

    # create arguments parser
    parser = argparse.ArgumentParser(description='Download the raw data files from data sources')

    # add the date
    parser.add_argument("--date", type=str, 
        help="Specify the date (YYYY-MM-DD) to name the file")

    parser.add_argument("--mode", type=str, 
        choices=['loop_cdcvac', 'none'], default='none',
        help="Run downloader as a cron service for CDC VAC?")

    # add the source for downloading
    parser.add_argument("--ds", type=str, 
        choices=[
            'usafacts', 'covidtracking', 'jhu', 'cdcpvi', 
            'cdcvac_now', 
            'jhucci_vax',
            'actnow',
            'nytimes',
            'owidvac',
            'all'], 
        help="Specify which source to download (usafacts, covidtracking, jhu, cdcpvi), by default download all")
    # parse the input parameter
    args = parser.parse_args()

    parse_date = None
    if args.date is not None:
        parse_date = args.date

    if args.mode == 'loop_cdcvac':
        tl.start(block=True)
    else:
        if 'usafacts' in args.ds or args.ds == 'all':
            download_county_data_from_usafact(parse_date)
            print('* done downloading all usafacts data files')

        if 'covidtracking' in args.ds or args.ds == 'all':
            download_usa_data_from_covidtracking(parse_date)
            download_state_data_from_covidtracking(parse_date)
            print('* done downloading all covidtracking data files')

        if 'jhu' == args.ds or args.ds == 'all':
            download_state_data_from_jhu(parse_date)
            download_world_ts_data_from_jhu(parse_date)
            print('* done downloading and merging jhu data files')

        if 'cdcpvi' in args.ds or args.ds == 'all':
            download_allusa_data_from_cdcpvi(parse_date)
            print('* done downloading and merging cdcpvi data files')
            
        if 'cdcvac_now' in args.ds or args.ds == 'all':
            download_current_state_vac_data_from_cdvvac(parse_date)
            print('* done downloading cdcvac data file')

        if 'jhucci_vax' in args.ds or args.ds == 'all':
            download_usa_vax_data_from_jhucci(parse_date)
            print('* done downloading jhucci vax data file')

        if 'actnow' in args.ds or args.ds == 'all':
            download_state_data_from_actnow(parse_date)
            download_county_data_from_actnow(parse_date)
            print('* done downloading COVID Act Now data files')

        if 'nytimes' in args.ds or args.ds == 'all':
            download_usa_data_from_nytimes(parse_date)
            download_state_data_from_nytimes(parse_date)
            download_county_data_from_nytimes(parse_date)
            print('* done downloading NYTimes data files')

        if 'owidvac' in args.ds or args.ds == 'all':
            download_world_vax_data_from_owidvac(parse_date)
            print('* done downloading OurWorldInData data files')