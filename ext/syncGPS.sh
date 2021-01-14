#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2013
npfix=/zippy/MARS/targ/supl/UAF/radar/$year/larsen_nav
dpfix=/zippy/MARS/targ/supl/UAF/radar/$year/hdf5
cpfix=/zippy/MARS/code/supl/UAF/radar/hfproc/ext

python $cpfix/syncGPS.py $npfix $dpfix

rm job.txt


