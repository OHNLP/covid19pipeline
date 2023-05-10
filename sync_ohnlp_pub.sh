#!/bin/bash
FOLDER_BASE="../covid19-ohnlp-pub"

# get each page
cd web
python server.py --mode build_ohnlp

# cd $FOLDER_BASE
cd ../$FOLDER_BASE
NOW=`date`
git add -A
git commit -am "update at $NOW"
git push
cd ..
echo "$ done sync to GitHub"

echo "* done!"
