# -*- coding: utf-8 -*-
'''Server V2
The previous one has too many legacy codes.
This v2 is for reducing the load and start some new ideas for VA4H
'''
import os
import sys
import math
import json
import time
import random
import datetime
import subprocess
import pathlib

from flask import Flask
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import session
from flask import jsonify
from flask import send_from_directory

from flask_compress import Compress

import numpy as np
import pandas as pd

from werkzeug.utils import secure_filename

# import newshub as newshub_srv

HOST = '0.0.0.0'
PORT = 8082
DEBUG = True

PROJ_FOLDER = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.path.sep + ".")
DATA_FOLDER = os.path.join(PROJ_FOLDER, '../data/')
DATA_RAW_FOLDER = os.path.join(DATA_FOLDER, 'raw')
DATA_RST_FOLDER = os.path.join(DATA_FOLDER, 'rst')

if not os.path.exists(DATA_FOLDER):
    os.mkdir(DATA_FOLDER)
    print('* created project data folder: %s' % DATA_FOLDER)
    
if not os.path.exists(DATA_RAW_FOLDER):
    os.mkdir(DATA_RAW_FOLDER)
    print('* created project raw data folder: %s' % DATA_RAW_FOLDER)

if not os.path.exists(DATA_RST_FOLDER):
    os.mkdir(DATA_RST_FOLDER)
    print('* created project result data folder: %s' % DATA_RST_FOLDER)


app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'key-of-this-app-9x9d3-37ikx-2mkxj-9d20x'
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'

Compress(app)

@app.before_request
def before_request():
    pass


@app.after_request
def after_request(response):
    return response


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/index_rcf_pub')
@app.route('/index_rcf_pub.html')
def index_rcf_pub():
    return render_template('index_rcf_pub.html')


@app.route('/index_pure_pub')
@app.route('/index_pure_pub.html')
def index_pure_pub():
    return render_template('index_pure_pub.html')


@app.route('/vacrrw')
@app.route('/vacrrw.html')
def vacrrw():
    return render_template('vacrrw.html')


@app.route('/mchrr_dashboard')
@app.route('/mchrr_dashboard.html')
def mchrr_dashboard():
    return render_template('mchrr_dashboard.html')


@app.route('/world_dashboard')
@app.route('/world_dashboard.html')
def world_dashboard():
    return render_template('world_dashboard.html')


@app.route('/delta_dashboard')
@app.route('/delta_dashboard.html')
def delta_dashboard():
    return render_template('delta_dashboard.html')


###########################################################
# COVID Data files
###########################################################

@app.route('/covid_data/<fn>')
def covid_data(fn):
    if fn is None or fn == '':
        return 'error filename'

    # TODO secure check
    full_filename = os.path.join(DATA_RST_FOLDER, fn)

    # load json
    ret = json.load(open(full_filename))
    return jsonify(ret)


@app.route('/covid_data/v2/<fn>')
def covid_data_v2(fn):
    if fn is None or fn == '':
        return 'error filename'

    # TODO secure check
    full_filename = os.path.join(DATA_RST_FOLDER, 'v2', fn)

    # load json
    ret = json.load(open(full_filename))
    return jsonify(ret)


@app.route('/covid_data/dsvm/<fn>')
def covid_data_dsvm(fn):
    '''Load data for the migrated website for dsvm
    '''
    if fn is None or fn == '':
        return 'error filename'

    # TODO secure check
    full_filename = os.path.join(DATA_RST_FOLDER, 'dsvm', fn)

    # load json
    ret = json.load(open(full_filename))
    return jsonify(ret)


@app.route('/covid_data/state/<fn>')
def covid_date_state(fn):
    if fn is None or fn == '':
        return 'error filename'

    # TODO secure check
    full_filename = os.path.join(DATA_RST_FOLDER, 'state', fn)

    # load json
    ret = json.load(open(full_filename))
    return jsonify(ret)

###########################################################
# DSVM Data Dashboard
###########################################################

@app.route('/dsvm_dashboard')
@app.route('/dsvm_dashboard.html')
def dsvm_dashboard():
    regions = [
        ('jax', 'JAX'),
        ('phx', 'PHX'),
        ('rst', 'RST/SEMN'),
        ('nwwi', 'NWWI'),
        ('swmn', 'SWMN'),
        ('swwi', 'SWWI'),
    ]
    return render_template('dsvm/dsvm_dashboard_v2.html', regions=regions)

@app.route('/dsvm_cdtmap_county')
@app.route('/dsvm_cdtmap_county.html')
@app.route('/cdtmap_county.html')
def dsvm_cdtmap_county():
    return render_template('dsvm/cdtmap_county.html')


@app.route('/dsvm_cdtmap_state')
@app.route('/dsvm_cdtmap_state.html')
@app.route('/cdtmap_state.html')
def dsvm_cdtmap_state():
    return render_template('dsvm/cdtmap_state.html')


@app.route('/dsvm_cdtmap_world')
@app.route('/dsvm_cdtmap_world.html')
@app.route('/cdtmap_world.html')
def dsvm_cdtmap_world():
    return render_template('dsvm/cdtmap_world.html')


###########################################################
# Build
###########################################################
def build_ohnlp():
    '''
    Build the static website for test
    '''
    with app.test_client() as client:
        with app.app_context():
            for url in [
                ['/index_pure_pub.html', 'index.html'],
                ['/world_dashboard.html', 'world_dashboard.html']
                ]:
                make_page(
                    client, 
                    url[0], 
                    os.path.join(
                        pathlib.Path(__file__).parent.absolute(),
                        '../',
                        '../',
                        'covid19-ohnlp-pub',
                        url[1]
                    )
                )

    print('* done building static pages')


def build_rcf():
    '''
    Build the static website for test
    '''
    with app.test_client() as client:
        with app.app_context():
            for url in [
                ['/index_pure_pub.html', 'index.html'],
                ['/mchrr_dashboard.html', 'mchrr_dashboard.html'],
                ['/delta_dashboard.html', 'delta_dashboard.html']
                ]:
                make_page(
                    client, 
                    url[0], 
                    os.path.join(
                        pathlib.Path(__file__).parent.absolute(),
                        '../',
                        '../',
                        'html',
                        url[1]
                    )
                )

    print('* done building static pages')


def make_page(client, url, path, param=None):
    '''
    Make static page from url
    '''
    rv = client.get(url)
    with open(path, 'w') as f:
        f.write(rv.data.decode('utf8'))
    
    print('* made static page %s' % (path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='COVID-19 Dashboards')

    # add paramters
    parser.add_argument("--mode", type=str, 
        choices=['build_ohnlp', 'build_rcf', 'run'], default='run',
        help="Which mode are you going to take?")

    args = parser.parse_args()

    if args.mode == 'run':
        app.run(host=HOST, port=PORT)

    elif args.mode == 'build_ohnlp':
        build_ohnlp()

    elif args.mode == 'build_rcf':
        build_rcf()

    else:
        parser.print_usage()
