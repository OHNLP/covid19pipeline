#!/bin/bash
work_path=$(dirname $(readlink -f $0))
echo "* work_path: $work_path"

cp -r $work_path/../data/rst/* $work_path/../../html/covid_data/
echo "* copied all data files"