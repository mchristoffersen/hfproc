#!/bin/bash

# First arg is a text file where each line is the name of a nav file

# Build las loc index
# Build las db

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

year=2017
ipfix=/zippy/MARS/targ/supl/UAF/$year/hdf5
spfix=/zippy/MARS/orig/supl/UAF/lidar/$year
cpfix=/zippy/MARS/code/xped/hfproc/ext
math_op=median

for p in $ipfix/*.h5;
do
    echo "python $cpfix/fresnelElev.py $spfix $p $math_op" >> ./job.txt
done

parallel -j 44 < ./job.txt

rm job.txt
