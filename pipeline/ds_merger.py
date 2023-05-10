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
import pathlib
import datetime
import argparse

import pandas as pd
print('* loaded packages!')

from tqdm import tqdm

import ds_config as cfg

###############################################################################
# The V2 functions
###############################################################################

#%% main functions
def merge_states_v2(parse_date=None):
    '''
    Merge state level JSON file v2
    '''
    # get the date if it's None
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)

    print("""
    ###############################################################
    # Merge STATE %s JSON files
    ###############################################################
    """ % (parse_date))

    # get the calc version
    calc = 'v2'

    # get list
    dft = pd.read_csv(cfg.FN_STATE_POPU)
    dft.set_index('FIPS', inplace=True)

    # get all files
    folder_parsed_files = os.path.join(cfg.FOLDER_PRS, calc, parse_date)
    if not os.path.exists(folder_parsed_files):
        print('* NOT found %s' % folder_parsed_files)
        return

    # get all the data files in the parsed folder
    fns = os.listdir(folder_parsed_files)
    print('* found %s files' % (
        len(fns)
    ))
    
    for idx, row in dft.iterrows():
        FIPS = idx
        FIPS = '%s' % FIPS if FIPS > 9 else '0%s' % FIPS
        state = row['ABBR']

        if state == 'US': continue

        j = {
            "geo": "state",
            "state": state,
            "date": parse_date,
            "county_data": {},
            "dates": None,
            "state_data": None,
            "usa_data": None
        }

        # Now, fill the missing parts!
        # add the county_data
        cnt_counties = 0
        for fn in fns:
            if fn.startswith('USA-%s' % FIPS):
                countyFIPS = fn[4:4+5]
                tmp = json.load(open(os.path.join(folder_parsed_files, fn)))
                del tmp['dates']
                j['county_data'][countyFIPS] = tmp
                cnt_counties += 1

        # special rule for the 5 territories
        # since we don't have the county level data
        if state in ["AS", "GU", "MP", "PR", "VI"]:
            # just set the FIPS as the first item
            tFIPS = '%s001' % FIPS

            # load the state-level data and reset the FIPS
            tmp = json.load(open(os.path.join(folder_parsed_files, 'USA-%s.json' % state)))
            del tmp['dates']
            tmp['FIPS'] = tFIPS

            # put state-level data as the county-level data
            j['county_data'][tFIPS] = tmp

        # add the state_data
        tmp = json.load(open(os.path.join(folder_parsed_files, 'USA-%s.json' % state)))
        del tmp['dates']
        j['state_data'] = tmp

        # add the usa_data
        tmp = json.load(open(os.path.join(folder_parsed_files, 'WORLD-USA.json')))
        dates = tmp['dates']
        del tmp['dates']
        j['usa_data'] = tmp
        
        # add the dates
        j['dates'] = dates

        # add the last update
        j['last_update_date'] = datetime.datetime.today().strftime('%Y-%m-%d')
        j['last_update_date_str'] = datetime.datetime.today().strftime('%b %-d, %Y')

        # create folder if not exists
        folder_output_json = cfg.FOLDER_RST_V2
        if not os.path.exists(folder_output_json):
            os.makedirs(folder_output_json, exist_ok=True)

        # save json for this county
        fn_web_json = os.path.join(
            folder_output_json, cfg.FN_OUTPUT_STATE % state
        )
        json.dump(j, open(fn_web_json, 'w'))
        print('* merged %s %s data with %s counties' % (parse_date, state, cnt_counties))

    print('* merged all %s states data %s' % (len(dft), parse_date))


def merge_usa_v2(parse_date=None):
    '''
    Merge the USA whole data v2
    '''
    # get the date if it's None
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)

    print("""
    ###############################################################
    # Merge USA %s JSON file %s
    ###############################################################
    """ % (parse_date, cfg.FN_OUTPUT_USA))

    # get the calc version
    calc = 'v2'

    # get list
    dft = pd.read_csv(cfg.FN_STATE_POPU)
    dft.set_index('FIPS', inplace=True)

    # get all files
    folder_parsed_files = os.path.join(cfg.FOLDER_PRS, calc, parse_date)
    if not os.path.exists(folder_parsed_files):
        print('* NOT found %s' % folder_parsed_files)
        return

    # create the output json
    j = {
        "geo": "country",
        "states": [],
        "date": parse_date,
        "dates": None,
        "state_data": {},
        "usa_data": None
    }
    for idx, row in dft.iterrows():
        state = row['ABBR']
        if state == 'US': continue

        # add the state
        j['states'].append(state)

        # add the state_data
        tmp = json.load(open(os.path.join(folder_parsed_files, 'USA-%s.json' % state)))
        del tmp['dates']
        
        j['state_data'][state] = tmp

    # add the usa_data
    tmp = json.load(open(os.path.join(folder_parsed_files, 'WORLD-USA.json')))
    dates = tmp['dates']

    del tmp['dates']

    # add the usa data
    j['usa_data'] = tmp

    # add the dates
    j['dates'] = dates

    # add the last update
    j['last_update_date'] = datetime.datetime.today().strftime('%Y-%m-%d')
    j['last_update_date_str'] = datetime.datetime.today().strftime('%b %-d, %Y')

    # create folder if not exists
    folder_output_json = cfg.FOLDER_RST_V2
    if not os.path.exists(folder_output_json):
        os.makedirs(folder_output_json, exist_ok=True)

    # save json for this county
    fn_web_json = os.path.join(folder_output_json, cfg.FN_OUTPUT_USA)
    json.dump(j, open(fn_web_json, 'w'))
    print('* merged USA data %s to %s' % (parse_date, fn_web_json))


def merge_world_v2(parse_date=None):
    '''
    Merge the whole world data v2
    '''
    # get the date if it's None
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)

    print("""
    ###############################################################
    # Merge World %s JSON file %s
    ###############################################################
    """ % (parse_date, cfg.FN_OUTPUT_WORLD))

    # get the calc version
    calc = 'v2'

    # get all files
    folder_parsed_files = os.path.join(cfg.FOLDER_PRS, calc, parse_date)
    if not os.path.exists(folder_parsed_files):
        print('* NOT found %s' % folder_parsed_files)
        return

    # get all the data files in the parsed folder
    fns = os.listdir(folder_parsed_files)    

    # create the output json
    j = {
        "geo": "world",
        "date": parse_date,
        "dates": [],
        "world_data": {}
    }
    for fn in tqdm(fns):
        if not fn.startswith('WORLD-'):
            continue
        
        # add the data of this country
        tmp = json.load(open(os.path.join(folder_parsed_files, fn)))
        FIPS = tmp['FIPS']
        
        # use the date of USA
        if FIPS == 'USA': j['dates'] = tmp['dates']

        # remove the dates
        del tmp['dates']
        
        # add the state
        j['world_data'][FIPS] = tmp

    # add the last update
    j['last_update_date'] = datetime.datetime.today().strftime('%Y-%m-%d')
    j['last_update_date_str'] = datetime.datetime.today().strftime('%b %-d, %Y')

    # create folder if not exists
    folder_output_json = cfg.FOLDER_RST_V2
    if not os.path.exists(folder_output_json):
        os.makedirs(folder_output_json, exist_ok=True)

    # save json for this county
    fn_web_json = os.path.join(folder_output_json, cfg.FN_OUTPUT_WORLD)
    json.dump(j, open(fn_web_json, 'w'))
    print('* merged WORLD data %s to %s' % (parse_date, fn_web_json))


def merge_mchrr_v2(parse_date=None):
    '''
    Merge the whole MCHRR data v2
    '''
    # get the date if it's None
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    if parse_date == None:
        parse_date = yesterday.strftime('%Y-%m-%d')
        print("* set parse_date=%s" % parse_date)

    print("""
    ###############################################################
    # Merge MCHRR %s JSON file %s
    ###############################################################
    """ % (parse_date, cfg.FN_OUTPUT_MCHRR))

    # get the calc version
    calc = 'v2'

    # get all files
    folder_parsed_files = os.path.join(cfg.FOLDER_PRS, calc, parse_date)
    if not os.path.exists(folder_parsed_files):
        print('* NOT found %s' % folder_parsed_files)
        return

    # get all the data files in the parsed folder
    fns = os.listdir(folder_parsed_files)    

    # create the output json
    j = {
        "geo": "mchrr",
        "date": parse_date,
        "dates": [],
        "usa_data": {},
        "state_data": {},
        "mchrr_data": {},
        "county_data": {}
    }

    for fn in tqdm(fns):
        if fn.startswith('MCHRR-'):
            # add the data of this region
            tmp = json.load(open(os.path.join(folder_parsed_files, fn)))
            FIPS = tmp['FIPS']

            # remove the dates
            del tmp['dates']
            
            # add the state
            j['mchrr_data'][FIPS] = tmp

        elif fn.startswith('USA-MN') or \
            fn.startswith('USA-WI') or \
            fn.startswith('USA-FL') or \
            fn.startswith('USA-AZ'):

            # add the data of this state
            tmp = json.load(open(os.path.join(folder_parsed_files, fn)))
            state = tmp['state']

            # remove the dates
            del tmp['dates']
            
            # add the state
            j['state_data'][state] = tmp

        elif fn.startswith('WORLD-USA'):

            # add the data of this state
            tmp = json.load(open(os.path.join(folder_parsed_files, fn)))
            state = tmp['state']
            j['dates'] = tmp['dates']

            # remove the dates
            del tmp['dates']
            
            # add the state
            j['usa_data'] = tmp

        elif fn.startswith('USA-') and len(fn) > 12:
            countyFIPS = fn[4:4+5]

            if countyFIPS not in cfg.MC_HRR_COUNTIES_5DS:
                continue

            # it's a county!
            tmp = json.load(open(os.path.join(folder_parsed_files, fn)))
            _fips = tmp['FIPS']

            # remove the dates
            del tmp['dates']
            
            # add the state
            j['county_data'][_fips] = tmp

        else:
            continue

    # add the last update
    j['last_update_date'] = datetime.datetime.today().strftime('%Y-%m-%d')
    j['last_update_date_str'] = datetime.datetime.today().strftime('%b %-d, %Y')

    # create folder if not exists
    folder_output_json = cfg.FOLDER_RST_V2
    if not os.path.exists(folder_output_json):
        os.makedirs(folder_output_json, exist_ok=True)

    # save json for this county
    fn_web_json = os.path.join(folder_output_json, cfg.FN_OUTPUT_MCHRR)
    json.dump(j, open(fn_web_json, 'w'))
    print('* merged WORLD data %s to %s' % (parse_date, fn_web_json))


if __name__ == "__main__":
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    parse_date = yesterday.strftime('%Y-%m-%d')

    # create arguments parser
    parser = argparse.ArgumentParser(description='Merge the parsed results in the date folder to final JSON file')
    parser.add_argument("--calc", type=str,
        choices=['v2'], default='v2',
        help="Which version of calculation? v2 or v2?")
    parser.add_argument("--lv", type=str,
        choices=['state', 'usa', 'world', 'mchrr', 'all'], default='all',
        help="Which level of JSON to produce? state-level, USA-level, mchrr, or all levels?")
    parser.add_argument("--date", type=str, 
        help="Specify the date (YYYY-MM-DD) to merge, empty is %s" % parse_date)

    # parse the input parameter
    args = parser.parse_args()

    if args.date is not None:
        parse_date = args.date

    result_path = os.path.join(
        cfg.FOLDER_PRS, args.calc, parse_date
    )
    if os.path.exists(result_path):
        if args.lv == 'all' or 'state' in args.lv:
            merge_states_v2(parse_date)
            print('* merged the state level data')
        if args.lv == 'all' or 'usa' in args.lv:
            merge_usa_v2(parse_date)
            print('* merged the USA level data')
        if args.lv == 'all' or 'world' in args.lv:
            merge_world_v2(parse_date)
            print('* merged the world level data')
        if args.lv == 'all' or 'mchrr' in args.lv:
            merge_mchrr_v2(parse_date)
            print('* merged the mchrr level data')
            
    else:
        print('* NOT found the specified date %s results data in %s' % (
            parse_date, result_path
        ))
