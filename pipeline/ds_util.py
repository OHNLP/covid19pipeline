import os
import math
import json
import datetime
import argparse

import wget

import numpy as np

from tqdm import tqdm
import pandas as pd

import ds_config as cfg


def download_jhu_raw_world_data_by_date(dt):
    '''
    Download the JHU world data

    Args:

    dt: date start YYYY-MM-DD
    '''
    if not os.path.exists(cfg.FOLDER_SRC_JHU_RAW):
        os.makedirs(cfg.FOLDER_SRC_JHU_RAW, exist_ok=True)
        
    date = pd.date_range(dt, dt)[0]
    dt_fn = date.strftime('%m-%d-%Y')

    url = cfg.DS_JHU_WORLD % dt_fn

    # create the fn for save
    dt_save_fn = date.strftime('%Y-%m-%d')
    save_raw_fn = cfg.FN_SAVE_JHU_WORLD_RAW_DATA % dt_save_fn

    # check if exists
    if os.path.exists(save_raw_fn):
        print('* %s data exists %s' % (dt_save_fn, save_raw_fn))
    else:
        wget.download(url, save_raw_fn)
        print('* done downloading %s to %s' % (dt, save_raw_fn))


def download_jhu_raw_world_data_by_date_range(ds, de):
    '''
    Download the JHU world data

    Args:

    ds: date start YYYY-MM-DD
    de: date end YYYY-MM-DD
    '''

    if not os.path.exists(cfg.FOLDER_SRC_JHU_RAW):
        os.makedirs(cfg.FOLDER_SRC_JHU_RAW, exist_ok=True)

    dates = pd.date_range(ds, de)

    for date in tqdm(dates):
        # get the url for this date
        dt_fn = date.strftime('%m-%d-%Y')
    
        url = cfg.DS_JHU_WORLD % dt_fn

        # create the fn for save
        dt_save_fn = date.strftime('%Y-%m-%d')
        save_raw_fn = cfg.FN_SAVE_JHU_WORLD_RAW_DATA % dt_save_fn

        # check if exists
        if os.path.exists(save_raw_fn):
            continue


        # download
        wget.download(url, save_raw_fn)

    print('* done downloading from %s to %s' % (ds, de))


if __name__ == "__main__":
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    date = yesterday.strftime('%Y-%m-%d')

    # create arguments parser
    parser = argparse.ArgumentParser(description='Detect where the actual data of specified date are updated')
    # the action
    parser.add_argument("--task", type=str,
        choices=['download_jhu'], default='download_jhu',
        help="Download JHU data")
    # the date
    parser.add_argument("--date", type=str, 
        help="Specify the date (YYYY-MM-DD) to parse, empty is %s" % date)

    # parse the input parameter
    args = parser.parse_args()

    if args.date is None:
        args.date = date
    
    download_jhu_raw_world_data_by_date(args.date)


def _calc_cdt(ncc, ncc_past):
    '''
    Calculate the CDT
    '''
    if ncc_past == 0:
        return 0

    return cfg.N_CDT_SMOOTH_DAYS * np.log(2) / np.log((ncc + 0.5) / ncc_past)


def _calc_crt(ncc, ncc_7, ncc_14):
    '''
    Calculate the RW_Cr7d100k
    '''
    if ncc_7 - ncc_14 == 0:
        return 0
    else:
        return (ncc - ncc_7) / (ncc_7 - ncc_14)


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