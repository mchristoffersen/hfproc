#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ipfix=/zippy/MARS/orig/supl/UAF/radar/2019
opfix=/zippy/MARS/targ/supl/UAF/2019/hdf5
cpfix=/zippy/MARS/code/xped/hfProc/raw2h5

for p in $ipfix/*.dat;
do
    echo "python $cpfix/lowres2h5.py $p $opfix/" >> ./job.txt
done

parallel -j 40 < ./job.txt

rm job.txt


