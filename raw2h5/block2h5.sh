#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ipfix=/zippy/MARS/targ/supl/UAF/2018/aug/block_clutter
opfix=/home/btober/proj/hfproc/raw2h5/test
cpfix=/zippy/MARS/code/xped/hfproc/raw2h5

#for p in $ipfix/*.mat;
#do
#    echo "python $cpfix/block2h5.py $p $opfix/" >> ./job.txt
#done

#parallel -j 40 < ./job.txt

#rm job.txt

python $cpfix/block2h5.py $ipfix/20180817-044158 $opfix
