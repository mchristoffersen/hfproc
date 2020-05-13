#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

cpfix=/zippy/MARS/code/xped/hfProc/drv
dpfix=/zippy/MARS/code/modl/simc/out/ak2018
ipfix=/zippy/MARS/targ/supl/UAF/2018/hdf5

for p in $dpfix/*_combined.img;
do
    echo "python $cpfix/addClutter.py $p $ipfix" >> ./job.txt
done

parallel -j 35 < ./job.txt

rm job.txt


