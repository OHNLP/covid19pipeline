'''DS Watcher
Check the data update in USAFacts
'''
__author__ = 'Huan He'
__version__ = '0.2.9'

import os
import sys
sys.path.insert(0, '.')
from pprint import pprint
import time
import pathlib
import subprocess
from importlib import reload
import argparse

from timeloop import Timeloop
from datetime import timedelta
from datetime import datetime
from datetime import timedelta
from termcolor import colored

import ds_detector
import get_crrw_latest_v5c as get_crrw_latest
import get_pvi_latest

import logging
logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger("watcher")
logger.setLevel(logging.INFO)

tl = Timeloop()

ds_uf_ret = {}
ds_tp_ret = {}
ds_cdcpvi_ret = {}

g_last_dt_crrw = None
g_last_dt_pvi = None
g_last_parse_date = None

post_task = 'none'
tasks = []


@tl.job(interval=timedelta(seconds=120))
def update_cdcpvi_data():
    '''
    Check the data source of CDC PVI and update!
    '''
    dt = datetime.now()
    parse_date = (dt-timedelta(days=1)).strftime('%Y-%m-%d')

    global ds_cdcpvi_ret
    global g_last_dt_pvi

    # it's working hour!
    g_last_dt_pvi = dt

    if ds_cdcpvi_ret == {}:
        ret = ds_detector.detect_ds_cdcpvi(parse_date)
    elif ds_cdcpvi_ret['flag_cdcpvi']:
        # double check if the date is correct
        if ds_cdcpvi_ret['check_date'] == parse_date:
            # no need to update
            logger.info('CDC PVI data of %s are %s!' % (
                ds_cdcpvi_ret['check_date'], 'already updated'
            ))
            return
        else:
            ret = ds_detector.detect_ds_cdcpvi(parse_date)
    else:
        ret = ds_detector.detect_ds_cdcpvi(parse_date)

    ds_cdcpvi_ret = ret
    
    # now need to update the CDC PVI data
    if ds_cdcpvi_ret['flag_cdcpvi']:
        logger.info('CDC PVI data of %s are %s!' % (
            ret['check_date'], colored('UPDATED', 'white', 'on_green', attrs=['bold'])
        ))
    else:
        # OK, not updated
        logger.info('CDC PVI data of %s is [%s]' % (
            ret['check_date'],
            colored('NOT YET', 'red'),
        ))
        return

    time.sleep(3)

    # now! let's do the update
    get_pvi_latest.update_pvi_by_date_str(parse_date)
    logger.info('Updated CDC PVI data of %s!' % parse_date)


@tl.job(interval=timedelta(seconds=180))
def detect_crrw_data():
    '''
    detect the data source of USAFacts and update!
    '''
    dt = datetime.now()
    dt_check = (dt-timedelta(days=1)).strftime('%-m/%-d/%y')
    parse_date = (dt-timedelta(days=1)).strftime('%Y-%m-%d')

    global ds_cdcpvi_ret
    global ds_uf_ret
    global ds_tp_ret

    global g_last_parse_date
    global g_last_dt_crrw
    global post_task

    if g_last_parse_date is None:
        # OK, data is not updated yet
        logger.info('Not detect %s CrRW data source yet, will detect soon' % parse_date)
    elif g_last_parse_date == parse_date:
        # OK, has updated
        logger.info('Has updated %s JSON files.' % parse_date)
        return
    else:
        # OK, need to update
        logger.info('Not updated %s data, last update is %s' % (parse_date, g_last_parse_date))

    # detect the changes of USAFacts
    if ds_uf_ret == {}:
        ret_usaf = ds_detector.detect_ds_usafacts(parse_date)
    elif ds_uf_ret['flag_covid'] and ds_uf_ret['flag_death']:
        if ds_uf_ret['check_date'] == dt_check:
            # no need to update
            logger.info('Both USAFacts COVID and DEATH data of %s are %s!' % (
                ds_uf_ret['check_date'], 'already updated'
            ))
            return
        else:
            ret_usaf = ds_detector.detect_ds_usafacts(parse_date)
    else:
        ret_usaf = ds_detector.detect_ds_usafacts(parse_date)

    ds_uf_ret = ret_usaf

    # detect the changes of COVID Tracking
    if ds_tp_ret == {}:
        ret_cvdt = ds_detector.detect_ds_covidtracking(parse_date)
    elif ds_tp_ret['flag_state_covid'] and ds_tp_ret['flag_usa_covid']:
        if ds_tp_ret['check_date'] == dt_check:
            # no need to update
            logger.info('Both USAFacts COVID and DEATH data of %s are %s!' % (
                ds_tp_ret['check_date'], 'already updated'
            ))
            return
        else:
            ret_cvdt = ds_detector.detect_ds_covidtracking(parse_date)
    else:
        ret_cvdt = ds_detector.detect_ds_covidtracking(parse_date)

    ds_tp_ret = ret_cvdt

    # show the result
    ds_detector.show_all_rets(parse_date, ds_cdcpvi_ret, ds_uf_ret, ds_tp_ret)


@tl.job(interval=timedelta(seconds=210))
def update_crrw_data():
    '''
    Check the data source of USAFacts and update!
    '''
    dt = datetime.now()
    dt_check = (dt-timedelta(days=1)).strftime('%-m/%-d/%y')
    parse_date = (dt-timedelta(days=1)).strftime('%Y-%m-%d')
    global ds_uf_ret
    global ds_tp_ret
    global g_last_dt_crrw
    global g_last_parse_date
    global post_task
    global tasks
    
    # check has updated or not
    if g_last_parse_date is None:
        # OK, data is not updated yet
        pass
    elif g_last_parse_date == parse_date:
        # OK, has updated
        return
    else:
        # OK, need to update
        pass

    # check the data source status
    if ds_uf_ret == {} or ds_tp_ret == {}:
        return

    if ds_uf_ret['flag_covid'] and \
        ds_uf_ret['flag_death'] and \
        ds_tp_ret['flag_state_covid'] and \
        ds_tp_ret['flag_usa_covid']:
        # only do updating when everything is ready
        time.sleep(3)
    else:
        return
    
    # now! let's do the update
    if 'crrw' in tasks:
        get_crrw_latest.main()
        logger.info('Updated CrRW data!')

    # now! update the dsvm data sources
    if 'dsvm' in tasks:
        run_sh('update_dsvm_data.sh')
        logger.info('Updated DSVM data!')

    # update the flag
    g_last_parse_date = parse_date

    if post_task == 'to_local_rcf':
        # then copy to local rcf html folder
        to_local_rcf()
        logger.info('Copied to local rcf folder!')
    elif post_task == 'to_local_test':
        # then copy to local test html folder
        to_local_test()
        logger.info('Copied to local test folder!')
    elif post_task == 'to_pub_ohnlp':
        # then copy to local test html folder
        to_pub_ohnlp()
        logger.info('Copied to OHNLP repo folder!')
    else:
        logger.info('Nothing to do, finish!')


def to_local_rcf():
    run_sh('to_local_rcf.sh')


def to_local_test():
    run_sh('to_local_test.sh')


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
    parser = argparse.ArgumentParser(description='Watch the updates of USAFacts')

    parser.add_argument('--tasks', type=str,
        choices=['crrw+dsvm', 'crrw', 'dsvm'], default='crrw',
        help="What to do when data are ready?")

    parser.add_argument("--post_task", type=str, 
        choices=['to_pub_ohnlp', 'to_local_rcf', 'to_local_test', 'none'], default='to_pub_ohnlp',
        help="What to do after generating CrRW data? to_pub_ohnlp, to_local_rcf, to_local_test or none?")

    parser.add_argument('--run_once', type=str,
        choices=['cdcpvi', 'crrw'], 
        help="just test one job for one time.")

    args = parser.parse_args()
    post_task = args.post_task
    tasks = args.tasks.split('+')

    if args.run_once:
        if args.run_once == 'cdcpvi':
            update_crrw_data()
        elif args.run_once == 'crrw':
            update_cdcpvi_data()
    elif args.post_task:
        tl.start(block=True)
    else:
        parser.print_help()
