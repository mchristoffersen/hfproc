#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2015
cpfix=/zippy/MARS/code/xped/hfproc/drv
dpfix=/zippy/MARS/targ/supl/UAF/$year/sim
ipfix=/zippy/MARS/targ/supl/UAF/$year/hdf5

for p in $dpfix/*_combined.img;
do
    echo "python $cpfix/addClutter.py $p $ipfix" >> ./job.txt
done

parallel -j 35 < ./job.txt

rm job.txt


