#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2016
npfix=/zippy/MARS/targ/supl/UAF/$year/larsen_nav
dpfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
cpfix=/zippy/MARS/code/xped/hfproc/ext

python $cpfix/addNav.py $npfix $dpfix

rm job.txt


