#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ncore=10

year=2020
#ipfix=/silo/data/akOIB/colugo/$year/hdf5
#opfix=/silo/data/akOIB/colugo/$year/qlook
#cpfix=/home/mchristo/proj/akOIB/hfproc/qlook

ipfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
opfix=/zippy/MARS/targ/supl/UAF/$year/qlookClutter/
cpfix=/zippy/MARS/code/xped/hfproc/qlook

for p in $ipfix/*.h5;
do
    echo "python $cpfix/clutterQlook.py $p $opfix" >> ./job.txt
done

parallel -j $ncore < ./job.txt

rm job.txt

