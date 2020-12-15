#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2019
#ipfix=/zippy/MARS/orig/supl/UAF/radar/$year
#opfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
#cpfix=/zippy/MARS/code/xped/hfproc/raw2h5

ipfix=/home/mchristo/proj/akOIB/scratch/test
opfix=/home/mchristo/proj/akOIB/scratch/test
cpfix=/home/mchristo/proj/akOIB/hfproc/raw2h5

for p in $ipfix/*.dat;
do
    echo "python $cpfix/lowres2h5.py $p $opfix/" >> ./job.txt
done

parallel -j 40 < ./job.txt

rm job.txt


