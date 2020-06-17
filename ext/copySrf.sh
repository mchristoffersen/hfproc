#!/bin/bash

# First arg is a text file where each line is the name of a nav file

# Build las loc index
# Build las db

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

cpfix=/zippy/MARS/code/xped/hfproc/ext
srcpfix=/zippy/MARS/targ/supl/UAF/2018/hdf5
dstpfix=/zippy/MARS/targ/supl/UAF/2018/toffset/hdf5

for p in $dstpfix/*.h5;
do
    echo "python $cpfix/copySrf.py $srcpfix/$p $dstpfix/$p" >> ./job.txt
done

#parallel -j 35 < ./job.txt

#rm job.txt


