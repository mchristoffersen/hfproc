#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

#ipfix=/zippy/MARS/orig/supl/UAF/radar/2018/aug
#opfix=/zippy/MARS/targ/supl/UAF/2018/hdf5
#cpfix=/zippy/MARS/code/xped/hfproc/raw2h5

ipfix=/home/mchristo/proj/akOIB/scratch/test
opfix=/home/mchristo/proj/akOIB/scratch/test
cpfix=/home/mchristo/proj/akOIB/hfproc/raw2h5

for p in $ipfix/*.tdms;
do
    echo "python $cpfix/tdms2h5.py $p $opfix/" >> ./job.txt
done

parallel -j 40 < ./job.txt

rm job.txt


