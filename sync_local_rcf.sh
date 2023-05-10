#!/bin/bash

URL_BASE="http://localhost:8082"
CUR_PATH=$(dirname $(readlink -f $0))
FOLDER_BASE="$CUR_PATH/../html"

# get each page
curl "$URL_BASE/index_rcf_pub.html" -o "$FOLDER_BASE/index.html"
curl "$URL_BASE/mchrr_dashboard.html" -o "$FOLDER_BASE/mchrr_dashboard.html"
curl "$URL_BASE/world_dashboard.html" -o "$FOLDER_BASE/world_dashboard.html"

# copy JSONs
echo "* CUR_PATH: $CUR_PATH"

cp -r $CUR_PATH/data/rst/* $CUR_PATH/../html/covid_data/
echo "* copied all data files"