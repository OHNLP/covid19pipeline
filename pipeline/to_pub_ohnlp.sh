#!/bin/bash
FOLDER_BASE="../../covid19-ohnlp-pub"

# copy JSONs
cp -r ../data/rst/* $FOLDER_BASE/covid_data
echo "* copied all latest data"

# cd $FOLDER_BASE
cd $FOLDER_BASE
NOW=`date`
git add -A
git commit -am "update at $NOW"
git push
cd ..
echo "$ done sync to GitHub"

echo "* done!"
