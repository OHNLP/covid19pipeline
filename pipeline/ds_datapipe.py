#!/usr/bin/env python3

# Copyright (c) Huan He (He.Huan@mayo.edu)
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

'''DS Data Pipeline for COVID-19 Dashboard
Detect, download, parse and merge the COVID-19 data
for the COVID-19 Dashboard project
'''
__author__ = 'Huan He'
__version__ = '0.9.1'

import os
import sys
sys.path.insert(0, '.')
from pprint import pprint
import json

import time
import pathlib
import subprocess
from importlib import reload
import argparse

from timeloop import Timeloop
from datetime import timedelta
from datetime import datetime
from termcolor import colored

import ds_detector
import ds_downloader
import ds_parser
import ds_merger
import ds_config as cfg


import logging
logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger("Pipeline")
logger.setLevel(logging.INFO)

# the main loop obj
tl = Timeloop()

# the last parse_date
g_last_parse_date = None

# what to do in the last step
g_last = 'none'

# what steps?
g_steps = 'all'

# return of the 
g_ret_jhuw = None
g_ret_cdcp = None
g_ret_usaf = None
g_ret_cvdt = None


def pipeline(parse_date=None):
    '''
    The data pipeline for get the JSON files on specified data
    '''
    if parse_date is None:
        today = datetime.now()
        yesterday = today-timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')
    
    logger.info('* Running data pipeline for %s' % (parse_date))

    # 1. detect
    if g_steps == 'all' or 'detect' in g_steps:
        rets = []
        rets.append(ds_detector.detect_ds_jhu_usa(parse_date))        # 0
        rets.append(ds_detector.detect_ds_jhu_state(parse_date))      # 1
        rets.append(ds_detector.detect_ds_jhu_ts_world(parse_date))   # 2
        rets.append(ds_detector.detect_ds_cdcpvi(parse_date))         # 3
        rets.append(ds_detector.detect_ds_actnow_state(parse_date))   # 4
        rets.append(ds_detector.detect_ds_actnow_county(parse_date))  # 5
        rets.append(ds_detector.detect_ds_owidvac_world(parse_date))  # 6

        # the followings are not required
        rets.append(ds_detector.detect_ds_jhucci_vax(parse_date))
        rets.append(ds_detector.detect_ds_covidtracking_state(parse_date))
        rets.append(ds_detector.detect_ds_covidtracking_usa(parse_date))
        rets.append(ds_detector.detect_ds_usafacts_covid(parse_date))
        rets.append(ds_detector.detect_ds_usafacts_death(parse_date))
        rets.append(ds_detector.detect_ds_nytimes_usa(parse_date))
        rets.append(ds_detector.detect_ds_nytimes_state(parse_date))
        rets.append(ds_detector.detect_ds_nytimes_county(parse_date))

        ds_detector.show_detect_rs(parse_date, *rets)

        # if any of the data source is not ready, skip
        if not rets[0]['flag'] or \
            not rets[1]['flag'] or \
            not rets[2]['flag'] or \
            not rets[3]['flag'] or \
            not rets[4]['flag'] or \
            not rets[5]['flag'] or \
            not rets[6]['flag']:
            logger.info('* NOT ready for one of the top 7 data sources')
            return -1

    # 2. download
    if g_steps == 'all' or 'download' in g_steps:
        ds_downloader.download_state_data_from_jhu(parse_date)
        ds_downloader.download_world_ts_data_from_jhu(parse_date)
        ds_downloader.download_allusa_data_from_cdcpvi(parse_date)
        ds_downloader.download_state_data_from_actnow(parse_date)
        ds_downloader.download_county_data_from_actnow(parse_date)
        ds_downloader.download_world_vax_data_from_owidvac(parse_date)
        # ds_downloader.download_current_state_vac_data_from_cdvvac(parse_date)
        
        logger.info('* Downloaded all %s data files from our data sources' % parse_date)
        logger.info('*' * cfg.WIDTH_SEP_LINE)

    # 3. parse
    if g_steps == 'all' or 'parse' in g_steps:
        ds_parser.parse_county_with_actnow_and_cdcpvi_data_v2(parse_date)
        ds_parser.parse_state_with_cdcpvi_and_actnow_v2(parse_date)
        ds_parser.parse_country_with_jhu_and_owid_data_v2(parse_date)
        ds_parser.parse_mchrr_with_actnow_and_cdcpvi_data_v2(parse_date)

        logger.info('* Parsed all %s data files' % parse_date)
        logger.info('*' * cfg.WIDTH_SEP_LINE)

    # 4. merge
    if g_steps == 'all' or 'merge' in g_steps:
        ds_merger.merge_states_v2(parse_date)
        ds_merger.merge_usa_v2(parse_date)
        ds_merger.merge_world_v2(parse_date)
        ds_merger.merge_mchrr_v2(parse_date)

        logger.info('* Merged all %s STATE, USA, WORLD, and MCHRR JSON files' % parse_date)
        logger.info('*' * cfg.WIDTH_SEP_LINE)

    # 5. upload
    if g_steps == 'all' or 'upload' in g_steps:
        if g_last == 'to_local_rcf':
            # then upload to azure
            to_local_rcf()
            logger.info('* Uploaded to local RCF storage!')

        elif g_last == 'to_pub_ohnlp':
            # then upload to pub
            to_pub_ohnlp()
            logger.info('* Uploaded to GitHub Pages!')

        elif g_last == 'both':
            to_local_rcf()
            logger.info('* Uploaded to local RCF storage!')
            to_pub_ohnlp()
            logger.info('* Uploaded to GitHub Pages!')

        else:
            logger.info('* No need to upload!')

    print('* finished %s' % g_steps)
    return 0


@tl.job(interval=timedelta(hours=1))
def run_pipeline():
    '''Check the data source and run!
    '''
    global g_last_parse_date

    # the parse_date is yesterday
    today = datetime.now()
    yesterday = today-timedelta(days=1)
    parse_date = yesterday.strftime('%Y-%m-%d')

    # second check if data is not updated
    ret = 0
    if g_last_parse_date == parse_date:
        logger.info('* Already updated %s JSON files' % parse_date)

    try:
        ret = pipeline(parse_date)
    except Exception as err:
        logger.error('* Pipeline runtime error on %s data: %s' % (parse_date, err))
        ret = -10

    # 5. set g_last_parse_date
    if ret == 0:
        g_last_parse_date = parse_date
    else:
        logger.info('* Stoped pipeline for %s JSON files, try later' % parse_date)
        
    return ret


def to_local_rcf():
    run_sh('to_local_rcf.sh')


def to_pub_ohnlp():
    run_sh('to_pub_ohnlp.sh')


def run_sh(fn):
    fullpath = pathlib.Path(__file__).parent.absolute()
    proc = subprocess.Popen([
        os.path.join(fullpath, fn)
    ], stdout=subprocess.PIPE)

    # Poll process.stdout to show stdout live
    while True:
        output = proc.stdout.readline()
        if proc.poll() is not None:
            break
        if output:
            print(output.strip().decode('utf8'))
    rc = proc.poll()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='COVID-19 Map Data Pipeline')

    # add paramters
    parser.add_argument("--mode", type=str, 
        choices=['loop', 'once'], default='loop',
        help="Run this program in a loop* or just once?")
    parser.add_argument("--steps", type=str, 
        default='all',
        help="Run all steps or just some? detect,download,parse,merge,upload")
    parser.add_argument("--last", type=str, 
        choices=['to_pub_ohnlp', 'to_local_rcf', 'both', 'none'], default='to_pub_ohnlp',
        help="What to do after generating JSON files?")
    parser.add_argument("--date", type=str, 
        help="Only used in 'once' mode. Specify the date (YYYY-MM-DD) for parse_date to generate JSON files")

    args = parser.parse_args()
    g_last = args.last
    g_steps = args.steps

    if args.mode == 'loop':
        tl.start(block=True)
    elif args.mode == 'once':
        pipeline(args.date)
    else:
        parser.print_help()
