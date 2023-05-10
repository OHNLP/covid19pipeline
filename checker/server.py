#!/usr/bin/env python3

# Copyright (c) Huan He (He.Huan@mayo.edu)
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#
'''
The data checker website
'''
import os
import sys
import json
import time
import datetime
import pathlib

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import send_from_directory

HOST = '0.0.0.0'
PORT = 8086
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'key-of-this-app-0oxs3-72yXi-982JH-72usp'
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'


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


@app.route('/mapdata/<fn>')
def mapdata(fn):
    calc = request.args.get('calc')
    if calc is None:
        calc = 'v2'
        
    # j = json.load(open('../data/rst/state_' + calc + '/' + fn))
    # return jsonify(j)

    return send_from_directory('../data/rst/state_' + calc, fn)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
