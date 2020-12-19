#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ncore=36

year=2014
ipfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
cpfix=/zippy/MARS/code/xped/hfproc/drv
#ipfix=/silo/data/akOIB/colugo/$year/hdf5
#cpfix=/home/mchristo/proj/akOIB/hfproc/drv

for p in $ipfix/*.h5;
do
    echo "python $cpfix/pulseCompress.py $p" >> ./job.txt
done

parallel -j $ncore < ./job.txt

rm job.txt


