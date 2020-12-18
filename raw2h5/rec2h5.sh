#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ncore=38

year=2014
ipfix=/zippy/MARS/orig/supl/UAF/radar/$year/martin_rec
opfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
cpfix=/zippy/MARS/code/xped/hfproc/raw2h5

#ipfix=/silo/data/akOIB/colugo/$year/martin_rec
#opfix=/silo/data/akOIB/colugo/$year/hdf5
#cpfix=/home/mchristo/proj/akOIB/hfproc/raw2h5

#ipfix=/home/mchristo/proj/akOIB/scratch/test
#opfix=/home/mchristo/proj/akOIB/scratch/test
#cpfix=/home/mchristo/proj/akOIB/hfproc/raw2h5



for p in $ipfix/*.mat;
do
    echo "python $cpfix/rec2h5.py $p $opfix" >> ./job.txt
done

parallel -j $ncore < ./job.txt

rm job.txt


