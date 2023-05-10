#!/bin/bash

echo "* updating the world level data!"
python get_dsvm_world_latest.py

echo "* updating the state level data!"
python get_dsvm_state_latest.py

echo "* updating the county level data!"
python get_dsvm_county_latest.py

echo "* updating the mayo HRR data!"
python get_dsvm_mayo6_latest.py

echo "* updating the MC test data"
python get_dsvm_mayo6_tests_latest.py

echo "* done!"