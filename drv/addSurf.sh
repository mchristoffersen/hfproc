#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ipfix=/zippy/MARS/targ/supl/UAF/2017/hdf5
cpfix=/zippy/MARS/code/xped/hfproc/drv

for p in $ipfix/*.h5;
do
    echo "python $cpfix/addSurf.py $p" >> ./job.txt
done

parallel -j 35 < ./job.txt

rm job.txt


