#!/bin/bash

ipfix=/zippy/MARS/orig/supl/UAF/lidar/2020/

for p in $ipfix/*.la?;
do
    ofile=$(basename "$p")
    nsfile=${ofile// /}
    mv "$ipfix/$ofile" $ipfix/$nsfile
done
