#!/bin/bash
touch ./job.txt
rm -f ./job.txt
touch ./job.txt

ipfix=/zippy/MARS/orig/supl/UAF/lidar/2020/
opfix=/zippy/MARS/orig/supl/UAF/lidar/2020/bounds

for p in $ipfix/*.la?;
do
    ofile=$(basename "$p" | cut -d. -f1).sqlite
    echo "pdal tindex create --tindex $opfix/$ofile --filespec \"$p\" -f SQLite" >> ./job.txt
done

parallel -j 35 < ./job.txt

#pdal tindex create --tindex ./exercises/analysis/boundary/boundary.sqlite \
# --filespec ./exercises/analysis/density/uncompahgre.laz \
# -f SQLite

