#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

npfix=/zippy/MARS/targ/supl/UAF/2019/larsen_nav
dpfix=/zippy/MARS/targ/supl/UAF/2019/hdf5
cpfix=/zippy/MARS/code/xped/hfProc/ext

python $cpfix/addNav.py $npfix $dpfix

rm job.txt


