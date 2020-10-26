#!/bin/bash

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2020
ipfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
cpfix=/zippy/MARS/code/xped/hfproc/drv

for p in $ipfix/*.h5;
do
    echo "python $cpfix/filter.py $p" >> ./job.txt
done

parallel -j 35 < ./job.txt

rm job.txt


