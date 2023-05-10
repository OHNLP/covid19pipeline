#%% load packages
import os
import time
import math
import json
import random
import datetime
import dateutil
import pathlib
import argparse
import urllib.request

from functools import reduce

from tqdm import tqdm

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

print('* loaded packages!')

# define some variables
FULLPATH = pathlib.Path(__file__).parent.absolute()
print('* current file path: %s' % FULLPATH)
FOLDER_RAW = os.path.join(FULLPATH, '../data/raw')
FOLDER_RST = os.path.join(FULLPATH, '../data/rst')
FOLDER_ARX = os.path.join(FULLPATH, '../data/arx')
FOLDER_SRC = os.path.join(FULLPATH, '../data/src')

# the output
FN_OUTPUT_CNTY_CDCPVI_HIST = os.path.join(FOLDER_SRC, 'cdc', 'uscnty-cdcpvi-history.csv')
FN_OUTPUT_CNTY_CDCPVI_BTPL = os.path.join(FOLDER_RAW, 'uscnty-cdcpvi-blank-tpl.csv')

# the data sources
# CDC PVI data
DS_CDCPVI_RAW_DATA = "https://raw.githubusercontent.com/COVID19PVI/data/master/Model11.2/Model_11.2_%s_data.csv"
DS_CDCPVI_RST_DATA = "https://raw.githubusercontent.com/COVID19PVI/data/master/Model11.2/Model_11.2_%s_results.csv"


def init_pvi_history():
    dfh = pd.read_csv(FN_OUTPUT_CNTY_CDCPVI_BTPL)
    dfh.to_csv(FN_OUTPUT_CNTY_CDCPVI_HIST)
    print('* inited the %s to %s' % (FN_OUTPUT_CNTY_CDCPVI_BTPL, FN_OUTPUT_CNTY_CDCPVI_HIST))


def create_pvi_history(date_st=None, date_ed=None):
    if date_st is None: date_st = '2020-02-28'
    if date_ed is None: date_ed = datetime.datetime.today() - datetime.timedelta(days=1)
    dates = pd.date_range(date_st, date_ed)
    for date in dates:
        update_pvi_by_date(date)
        time.sleep(2)
    

def _get_cdcpvi_raw_data(date_str):
    fn_cdcpvi_raw_data = DS_CDCPVI_RAW_DATA % date_str
    df_raw = pd.read_csv(fn_cdcpvi_raw_data, skiprows=12)
    return df_raw


def _get_cdcpvi_rst_data(date_str):
    fn_cdcpvi_rst_data = DS_CDCPVI_RST_DATA % date_str
    df_rst = pd.read_csv(fn_cdcpvi_rst_data)
    return df_rst


def _get_cdcpvi_localdata():
    dfh = pd.read_csv(FN_OUTPUT_CNTY_CDCPVI_HIST)
    return dfh


def _sort_columns(cols):
    def _pad_zero(d):
        ps = d.split('/')
        return '%02d/%02d/%02d' % (
            int(ps[0]), int(ps[1]), int(ps[2])
        )
    
    def _rm_zero(d):
        ps = d.split('/')
        return '%d/%d/%02d' % (
            int(ps[0]), int(ps[1]), int(ps[2])
        )

    sortable_cols = list(map(_pad_zero, cols))
    sorted_cols = sorted(sortable_cols)
    rmed_cols = list(map(_rm_zero, sorted_cols))
    
    return rmed_cols


def update_pvi_by_date_str(date_str):
    '''
    Date str is YYYY-MM-DD
    '''
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return update_pvi_by_date(date)


def update_pvi_by_date(date):
    # get the date label in CDC PVI data and column name
    date_str = date.strftime('%Y%m%d')
    date_col = date.strftime('%-m/%-d/%y')

    # get the file name
    fn_cdcpvi_raw_data = DS_CDCPVI_RAW_DATA % date_str
    fn_cdcpvi_rst_data = DS_CDCPVI_RST_DATA % date_str

    # get the data from CDC repository
    try:
        df_raw = pd.read_csv(fn_cdcpvi_raw_data, skiprows=12)
        df_rst = pd.read_csv(fn_cdcpvi_rst_data)
    except Exception as err:
        print('* NOT FOUND %s data: %s %s' % \
            (date_str, fn_cdcpvi_raw_data, fn_cdcpvi_rst_data))
        return None

    # keep the data simple
    dft_raw = df_raw[['sid', 'casrn', 'name']]
    dft_rst = df_rst[['ToxPi Score', 'Name']]

    # merge on the name and Name ...
    dft = pd.merge(dft_raw, dft_rst, how='inner', 
                left_on="name", right_on='Name')

    # rename the columns to make it easy to understand
    dft.rename(columns={
        'casrn': 'countyFIPS',
        'Name': 'countyName',
        'sid': 'geo',
        'ToxPi Score': date_col
    }, inplace=True)
    del dft['name']
    dft.set_index('countyFIPS', inplace=True)

    # get the history data
    dfh = pd.read_csv(FN_OUTPUT_CNTY_CDCPVI_HIST, index_col='countyFIPS')

    if date_col in dfh.columns:
        print('* existed %s in %s' % (date_col, FN_OUTPUT_CNTY_CDCPVI_HIST))
    else:
        dfh = dfh.merge(dft.loc[:, [date_col]], left_index=True, right_index=True)
        print('* merged %s in %s' % (date_col, FN_OUTPUT_CNTY_CDCPVI_HIST))

    # sort the columns
    # 9/22/20: fixed the eating the first column
    cols = dfh.columns.tolist()
    sorted_columns = _sort_columns(cols)
    dfh = dfh.reindex(sorted_columns, axis=1)

    # save the merged results
    dfh.to_csv(FN_OUTPUT_CNTY_CDCPVI_HIST)
    return dfh


def update_pvi():
    today = datetime.datetime.today()
    ystdy = today - datetime.timedelta(days=1)

    today_str = today.strftime('%Y-%m-%d')
    ystdy_str = ystdy.strftime('%Y-%m-%d')
    print('* today is %s, need to get the %s' % (today_str, ystdy_str))
    r = update_pvi_by_date(ystdy)
    return r


def validate_date(date_text):
    try:
        if date_text != datetime.datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            return False
        return True
    except ValueError:
        return False

# %% main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get the CDC PVI dataset')

    parser.add_argument("--act", type=str, 
        choices=['init', 'make_all', 'daily_update', 'update_date'], default="daily_update",
        help="What to do with CDC PVI data? init, make_all, or daily_update")

    parser.add_argument("--date", type=str,
        help="the date of data to update, YYYY-MM-DD format")

    args = parser.parse_args()
    if args.act == 'init':
        init_pvi_history()
    elif args.act == 'make_all':
        create_pvi_history()
    elif args.act == 'daily_update':
        update_pvi()
    elif args.act == 'update_date':
        date_str = args.date
        if validate_date(date_str):
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            update_pvi_by_date(date)
        else:
            parser.print_usage()
    else:
        parser.print_usage()