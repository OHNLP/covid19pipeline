#%% load packages

import os
import sys
import datetime
import argparse

import requests
from termcolor import colored
from prettytable import PrettyTable

import pandas as pd

import ds_config as cfg


def detect_ds_jhucci_vax(parse_date=None):
    '''
    Detect the data source of JHU CCI Vaccination
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')
        dt = parse_date

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        df = pd.read_csv(cfg.DS_JHUCCI_VAX_USA)

        # convert date format
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].apply(lambda v: v.strftime('%Y-%m-%d'))

        latest_date = df['date'].max()
        # check
        cnt = sum(df['date']==dt)
        if cnt > 0:
            # which means at least 1 state has new data
            flag_jhucci = True
        else:
            flag_jhucci = False

        ret = {
            'success': True,
            'ds': 'JHU CCI VAX',
            'lvtp': 'USA/VAX',
            'check_date': dt,
            'errmsg': 'Found %s' % cnt,
            'latest_date': latest_date,
            'flag': flag_jhucci
        }
    
    except Exception as err:
        ret = {
            'success': False,
            'ds': 'JHU CCI VAX',
            'lvtp': 'USA/VAX',
            'check_date': dt,
            'errmsg': 'Server Err',
            'latest_date': 'NA',
            'flag': False
        }

    return ret
        

def detect_ds_cdcvac(parse_date=None):
    '''
    Detect the data source of CDC Vaccinations
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
    
    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        r = requests.get(cfg.DS_CDCVAC_STATE)
        j = r.json()
        dt_data = j['vaccination_data'][0]['Date']
        ret = {
            'success': True,
            'check_date': dt,
            'errmsg': 'OK' if dt_data == dt else 'Not yet',
            'latest_cdcvac': dt_data,
            'flag_cdcvac': dt_data == dt
        }
    except:
        ret = {
            'success': False,
            'check_date': dt,
            'errmsg': 'Server Err',
            'latest_cdcvac': 'NA',
            'flag_cdcvac': False
        }

    return ret


def detect_ds_jhu_usa(parse_date=None):
    '''
    Detect the data source of John Hopkins
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
        dt_fn = yesterday.strftime('%m-%d-%Y')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
        dt_fn = yesterday.strftime('%m-%d-%Y')

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))

    try:
        df = pd.read_csv(cfg.DS_JHU_WORLD_DAILY % dt_fn, nrows=2)
        flag_covid = True
        ret = {
            'success': True,
            'ds': 'JHU DAILY',
            'lvtp': 'USA/ALL',
            'check_date': dt,
            'errmsg': 'Data found',
            'latest_date': dt,
            'flag': True
        }
    except:
        ret = {
            'success': False,
            'ds': 'JHU DAILY',
            'lvtp': 'USA/ALL',
            'check_date': dt,
            'errmsg': '404 Err',
            'latest_date': 'NA',
            'flag': False
        }
        
    return ret


def detect_ds_jhu_state(parse_date=None):
    '''
    Detect the data source of John Hopkins state level
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
        dt_fn = yesterday.strftime('%m-%d-%Y')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
        dt_fn = yesterday.strftime('%m-%d-%Y')

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        df = pd.read_csv(cfg.DS_JHU_STATE_DAILY % dt_fn, nrows=2)
        flag_covid = True
        ret = {
            'success': True,
            'ds': 'JHU DAILY',
            'lvtp': 'State/ALL',
            'check_date': dt,
            'errmsg': 'Data found',
            'latest_date': dt,
            'flag': True
        }
    except:
        ret = {
            'success': False,
            'ds': 'JHU DAILY',
            'lvtp': 'State/ALL',
            'check_date': dt,
            'errmsg': '404 Err',
            'latest_date': 'NA',
            'flag': False
        }
        
    return ret


def detect_ds_jhu_ts_world(parse_date=None):
    '''
    Detect the data source of John Hopkins time series data
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
        dt_col = yesterday.strftime('%-m/%-d/%y')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
        dt_col = yesterday.strftime('%-m/%-d/%y')

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        df = pd.read_csv(cfg.DS_JHU_WORLD_TS_CONFIRMED, nrows=2)
        flag_covid = dt_col in df.columns
        ret = {
            'success': True,
            'ds': 'JHU TS',
            'lvtp': 'WORLD/ALL',
            'check_date': dt,
            'errmsg': 'Server OK',
            'latest_date': df.columns[-1],
            'flag': flag_covid
        }
    except:
        ret = {
            'success': False,
            'ds': 'JHU TS',
            'lvtp': 'WORLD/ALL',
            'check_date': dt,
            'errmsg': '404 Err',
            'latest_date': 'NA',
            'flag': False
        }
        
    return ret


def detect_ds_cdcpvi(parse_date=None):
    '''
    Detect the data source of CDC
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
        dt_fn = yesterday.strftime('%Y%m%d')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date
        dt_fn = yesterday.strftime('%Y%m%d')

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        df = pd.read_csv(cfg.DS_CDCPVI_RAW_DATA % dt_fn, nrows=2)
        flag_covid = True
        ret = {
            'success': True,
            'ds': 'CDC PVI',
            'lvtp': 'USA/ALL',
            'check_date': dt,
            'errmsg': 'Data found',
            'latest_date': dt,
            'flag': True
        }
    except:
        ret = {
            'success': False,
            'ds': 'CDC PVI',
            'lvtp': 'USA/ALL',
            'check_date': dt,
            'errmsg': '404 Err',
            'latest_date': 'NA',
            'flag': False
        }
        
    return ret


def detect_ds_usafacts_covid(parse_date=None):
    '''
    Detect data source USAFacts updates on cases
    '''
    
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%-m/%-d/%y')
        parse_date = yesterday.strftime('%Y-%m-%d')
    else:
        date_obj = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = date_obj.strftime('%-m/%-d/%y')

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        covid_data = pd.read_csv(cfg.DS_USAFACTS_CONFIRM, nrows=2)
        
        # get the latest data
        flag = parse_date in covid_data.columns

        ret = {
            'success': True,
            'ds': 'USAFacts',
            'lvtp': 'County/covid',
            'errmsg': 'Server OK.',
            'check_date': dt,
            'latest_date': covid_data.columns[-1],
            'flag': flag,
        }
    except Exception as err:
        ret = {
            'success': False,
            'ds': 'USAFacts',
            'lvtp': 'County/covid',
            'errmsg': 'Server ERR!',
            'check_date': dt,
            'latest_date': 'NA',
            'flag': False
        }

    return ret


def detect_ds_usafacts_death(parse_date=None):
    '''
    Detect data source USAFacts updates on deaths
    '''
    
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%-m/%-d/%y')
        parse_date = yesterday.strftime('%Y-%m-%d')
    else:
        date_obj = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = date_obj.strftime('%-m/%-d/%y')

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    try:
        df = pd.read_csv(cfg.DS_USAFACTS_DEATH, nrows=2)
        
        # get the latest data
        flag = parse_date in df.columns

        ret = {
            'success': True,
            'ds': 'USAFacts',
            'lvtp': 'County/death',
            'errmsg': 'Server OK.',
            'check_date': dt,
            'latest_date': df.columns[-1],
            'flag': flag,
        }
    except Exception as err:
        ret = {
            'success': False,
            'ds': 'USAFacts',
            'lvtp': 'County/death',
            'errmsg': 'Server ERR!',
            'check_date': dt,
            'latest_date': 'NA',
            'flag': False
        }

    return ret


def detect_ds_covidtracking_state(parse_date=None):
    '''
    Detect data source COVID-19 Tracking updates of states
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    # get the latest data, just first two rows
    try:
        df = pd.read_csv(cfg.DS_COVIDTRACKING_STATE, nrows=2)

        latest_date = '%s' % df.date.unique().max()
        d_latest_date = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
        flag = (yesterday - d_latest_date).days <= 0

        ret = {
            'success': True,
            'ds': 'COVID Tracking',
            'lvtp': 'State/ALL',
            'check_date': dt,
            'errmsg': 'Server OK',
            'latest_date': latest_date,
            'flag': flag,
        }
    except Exception as err:
        ret = {
            'success': False,
            'ds': 'COVID Tracking',
            'lvtp': 'State/ALL',
            'check_date': dt,
            'errmsg': 'Server OK',
            'latest_date': 'NA',
            'flag': False
        }

    return ret


def detect_ds_covidtracking_usa(parse_date=None):
    '''
    Detect data source COVID-19 Tracking updates of USA
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        dt = yesterday.strftime('%Y-%m-%d')
    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        dt = parse_date

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    # get the latest data, just first two rows
    try:
        df = pd.read_csv(cfg.DS_COVIDTRACKING_USA, nrows=2)

        latest_date = '%s' % df.date.unique().max()
        d_latest_date = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
        flag = (yesterday - d_latest_date).days <= 0

        ret = {
            'success': True,
            'ds': 'COVID Tracking',
            'lvtp': 'USA/ALL',
            'check_date': dt,
            'errmsg': 'Server OK',
            'latest_date': latest_date,
            'flag': flag,
        }
    except Exception as err:
        ret = {
            'success': False,
            'ds': 'COVID Tracking',
            'lvtp': 'USA/ALL',
            'check_date': dt,
            'errmsg': 'Server OK',
            'latest_date': 'NA',
            'flag': False
        }

    return ret


def detect_ds_actnow_county(parse_date=None):
    '''
    Detect data source COVID Act Now updates of USA County
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))

    # get the TS data from COVID
    try:
        df = pd.read_csv(cfg.DS_ACTNOW_TS_COUNTY)

        # check if the date row is available
        n_rows = (df.date == parse_date).sum()
        latest_date = df.date.max()

        if n_rows == 0:
            # this condition means the target date is not available
            ret = {
                'success': True,
                'ds': 'COVID Act Now',
                'lvtp': 'County/ALL',
                'check_date': parse_date,
                'errmsg': 'Not available',
                'latest_date': latest_date,
                'flag': False,
            }
        else:
            ret = {
                'success': True,
                'ds': 'COVID Act Now',
                'lvtp': 'County/ALL',
                'check_date': parse_date,
                'errmsg': 'Found %s' % n_rows,
                'latest_date': latest_date,
                'flag': True,
            }

    except Exception as err:
        ret = {
            'success': False,
            'ds': 'COVID Act Now',
            'lvtp': 'County/ALL',
            'check_date': parse_date,
            'errmsg': 'Network Err!',
            'latest_date': 'NA',
            'flag': False,
        }
    
    return ret


def detect_ds_actnow_state(parse_date=None):
    '''
    Detect data source COVID Act Now updates of USA
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
   
    # get the TS data from COVID
    try:
        df = pd.read_csv(cfg.DS_ACTNOW_TS_STATE)

        # check if the date row is available
        n_rows = (df.date == parse_date).sum()
        latest_date = df.date.max()

        if n_rows == 0:
            # this condition means the target date is not available
            ret = {
                'success': True,
                'ds': 'COVID Act Now',
                'lvtp': 'State/ALL',
                'check_date': parse_date,
                'errmsg': 'Not available',
                'latest_date': latest_date,
                'flag': False,
            }
        else:
            # this condition means the target date is available
            # count how many states are NaN
            n_nan = df.loc[df.date == parse_date, 'actuals.cases'].isna().sum()
            if n_nan > cfg.N_ACTNOW_NAN_STATES:
                # it means the 50 states have missing
                ret = {
                    'success': True,
                    'ds': 'COVID Act Now',
                    'lvtp': 'State/ALL',
                    'check_date': parse_date,
                    'errmsg': 'NaN of %s' % n_nan,
                    'latest_date': latest_date,
                    'flag': False,
                }
            else:
                # still some missing ... but it's ok, we can do that later
                ret = {
                    'success': True,
                    'ds': 'COVID Act Now',
                    'lvtp': 'State/ALL',
                    'check_date': parse_date,
                    'errmsg': 'NaN of %s' % n_nan,
                    'latest_date': latest_date,
                    'flag': True,
                }
    except Exception as err:
        ret = {
            'success': False,
            'ds': 'COVID Act Now',
            'lvtp': 'State/ALL',
            'check_date': parse_date,
            'errmsg': 'Network Err!',
            'latest_date': 'NA',
            'flag': False,
        }
    
    return ret


def detect_ds_nytimes_usa(parse_date=None):
    '''
    Detect data source NYTimes updates of USA
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        # truncate the hour and other
        today = today.replace(hour=0, minute=0, second=0, microsecond=0) 
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))
    
    # get the TS data from COVID
    try:
        df = pd.read_csv(cfg.DS_NYTIMES_LATEST_USA)

        # check if the date row is available
        latest_date = df.date.max()
        latest_dt = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
        if latest_dt >= yesterday:
            ret = {
                'success': True,
                'ds': 'NYTimes',
                'lvtp': 'USA/ALL',
                'check_date': parse_date,
                'errmsg': 'OK',
                'latest_date': latest_date,
                'flag': True,
            }
        else:
            ret = {
                'success': True,
                'ds': 'NYTimes',
                'lvtp': 'USA/ALL',
                'check_date': parse_date,
                'errmsg': 'Not available',
                'latest_date': latest_date,
                'flag': False,
            }
                
    except Exception as err:
        print(err)
        ret = {
            'success': False,
            'ds': 'NYTimes',
            'lvtp': 'USA/ALL',
            'check_date': parse_date,
            'errmsg': 'Network Err!',
            'latest_date': 'NA',
            'flag': False,
        }
    
    return ret


def detect_ds_nytimes_state(parse_date=None):
    '''
    Detect data source NY Times updates of states
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        # truncate the hour and other
        today = today.replace(hour=0, minute=0, second=0, microsecond=0) 
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))

    # get the TS data from COVID
    try:
        df = pd.read_csv(cfg.DS_NYTIMES_LATEST_STATE)

        # check if the date row is available
        latest_date = df.date.max()
        latest_dt = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
        if latest_dt >= yesterday:
            ret = {
                'success': True,
                'ds': 'NYTimes',
                'lvtp': 'State/ALL',
                'check_date': parse_date,
                'errmsg': 'OK',
                'latest_date': latest_date,
                'flag': True,
            }
        else:
            ret = {
                'success': True,
                'ds': 'NYTimes',
                'lvtp': 'State/ALL',
                'check_date': parse_date,
                'errmsg': 'Not available',
                'latest_date': latest_date,
                'flag': False,
            }
                
    except Exception as err:
        print(err)
        ret = {
            'success': False,
            'ds': 'NYTimes',
            'lvtp': 'State/ALL',
            'check_date': parse_date,
            'errmsg': 'Network Err!',
            'latest_date': 'NA',
            'flag': False,
        }
    
    return ret


def detect_ds_nytimes_county(parse_date=None):
    '''
    Detect data source NY Times updates of counties
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        # truncate the hour and other
        today = today.replace(hour=0, minute=0, second=0, microsecond=0) 
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))

    # get the TS data from COVID
    try:
        df = pd.read_csv(cfg.DS_NYTIMES_LATEST_COUNTY)

        # check if the date row is available
        latest_date = df.date.max()
        latest_dt = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
        if latest_dt >= yesterday:
            ret = {
                'success': True,
                'ds': 'NYTimes',
                'lvtp': 'County/ALL',
                'check_date': parse_date,
                'errmsg': 'OK',
                'latest_date': latest_date,
                'flag': True,
            }
        else:
            ret = {
                'success': True,
                'ds': 'NYTimes',
                'lvtp': 'County/ALL',
                'check_date': parse_date,
                'errmsg': 'Not available',
                'latest_date': latest_date,
                'flag': False,
            }
                
    except Exception as err:
        print(err)
        ret = {
            'success': False,
            'ds': 'NYTimes',
            'lvtp': 'County/ALL',
            'check_date': parse_date,
            'errmsg': 'Network Err!',
            'latest_date': 'NA',
            'flag': False,
        }
    
    return ret


def detect_ds_owidvac_world(parse_date=None):
    '''
    Detect data source Our World in Data Vaccination updates of countries
    '''
    if parse_date is None:
        today = datetime.datetime.today()
        # truncate the hour and other
        today = today.replace(hour=0, minute=0, second=0, microsecond=0) 
        yesterday = today - datetime.timedelta(days=1)
        parse_date = yesterday.strftime('%Y-%m-%d')

    else:
        yesterday = datetime.datetime.strptime(parse_date, '%Y-%m-%d')
        today = yesterday + datetime.timedelta(days=1)

    print('* running %s for %s' % (sys._getframe().f_code.co_name, parse_date))

    # get the TS data from COVID
    try:
        df = pd.read_csv(cfg.DS_OWIDVAC_WORLD)

        # check if the date row is available
        latest_date = df.date.max()
        latest_dt = datetime.datetime.strptime(latest_date, '%Y-%m-%d')

        # the n 
        n_countries = len(df.iso_code.unique())
        n_has_latest = df.loc[df.date == parse_date, 'total_vaccinations'].count()

        if latest_dt >= yesterday:
            ret = {
                'success': True,
                'ds': 'OWID VAC',
                'lvtp': 'WORLD/VAX',
                'check_date': parse_date,
                'errmsg': 'Found %s/%s' % (n_has_latest, n_countries),
                'latest_date': latest_date,
                'flag': True,
            }
        else:
            ret = {
                'success': True,
                'ds': 'OWID VAC',
                'lvtp': 'WORLD/VAX',
                'check_date': parse_date,
                'errmsg': 'Not available',
                'latest_date': latest_date,
                'flag': False,
            }
                
    except Exception as err:
        print(err)
        ret = {
            'success': False,
            'ds': 'OWID VAC',
            'lvtp': 'WORLD/VAX',
            'check_date': parse_date,
            'errmsg': 'Network Err!',
            'latest_date': 'NA',
            'flag': False,
        }
    
    return ret


def _c(v):
    if v:
        return colored('%s' % v, 'white', 'on_green', attrs=['bold'])
    else:
        return colored('%s' % v, 'red')


def show_detect_rs(date, *argv):
    '''
    Show the results
    '''
    table = PrettyTable([
        'Data Source', 'Level/Type', 'Target Date', 'Is Updated', 'Last Date', 'Other'
    ])

    for ret in argv:
        # each ret is a return from
        table.add_row([
            ret['ds'], 
            ret['lvtp'], 
            date, 
            _c(ret['flag']), 
            ret['latest_date'], 
            ret['errmsg']
        ])
    
    print(table)


if __name__ == "__main__":
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    date = yesterday.strftime('%Y-%m-%d')

    # create arguments parser
    parser = argparse.ArgumentParser(description='Detect where the actual data of specified date are updated')

    parser.add_argument("--ds", type=str, 
        choices=[
            'jhu', 'usafacts', 'cdcpvi', 'covidtracking', 
            'cdcvac', 'jhucci_vax', 'actnow', 'nytimes',
            'owidvac',
            'all'
        ], default='all',
        help="Which data source to detect? default is all")

    parser.add_argument("--date", type=str, 
        help="Specify the date (YYYY-MM-DD) to parse, empty is %s" % date)

    # parse the input parameter
    args = parser.parse_args()

    parse_date = None
    if args.date is not None:
        parse_date = args.date
        date = args.date

    # the result
    rets = []
    if 'all' == args.ds or 'jhu' in args.ds:
        ret_jhu = detect_ds_jhu_usa(parse_date)
        rets.append(ret_jhu)
        ret = detect_ds_jhu_state(parse_date)
        rets.append(ret)
        ret = detect_ds_jhu_ts_world(parse_date)
        rets.append(ret)

    if 'all' == args.ds or 'jhucci_vax' in args.ds:
        ret = detect_ds_jhucci_vax(parse_date)
        rets.append(ret)
    
    if 'all' == args.ds or 'usafacts' in args.ds:
        ret = detect_ds_usafacts_covid(parse_date)
        rets.append(ret)
        ret = detect_ds_usafacts_death(parse_date)
        rets.append(ret)
    
    if 'all' == args.ds or 'cdcpvi' in args.ds:
        ret_cdcpvi = detect_ds_cdcpvi(parse_date)
        rets.append(ret_cdcpvi)

    if 'all' == args.ds or 'covidtracking' in args.ds:
        ret = detect_ds_covidtracking_state(parse_date)
        rets.append(ret)
        ret = detect_ds_covidtracking_usa(parse_date)
        rets.append(ret)

    if 'all' == args.ds or 'actnow' in args.ds:
        ret = detect_ds_actnow_state(parse_date)
        rets.append(ret)
        ret = detect_ds_actnow_county(parse_date)
        rets.append(ret)
        
    if 'all' == args.ds or 'nytimes' in args.ds:
        ret = detect_ds_nytimes_usa(parse_date)
        rets.append(ret)
        ret = detect_ds_nytimes_state(parse_date)
        rets.append(ret)
        ret = detect_ds_nytimes_county(parse_date)
        rets.append(ret)

    if 'all' == args.ds or 'owidvac' in args.ds:
        ret = detect_ds_owidvac_world(parse_date)
        rets.append(ret)
        
    print('* the detect results of %s are shown in the following table:' % (date))
    show_detect_rs(date, *rets)
    
