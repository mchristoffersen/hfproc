#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2020
ipfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
opfix=/zippy/MARS/targ/supl/UAF/$year/qlook/
cpfix=/zippy/MARS/code/xped/hfproc/qlook

for p in $ipfix/*.h5;
do
    echo "python $cpfix/dataQlook.py $p $opfix" >> ./job.txt
done

parallel -j 35 < ./job.txt

rm job.txt

