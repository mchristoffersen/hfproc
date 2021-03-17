import logging as log, sys, argparse, os
import h5py
import numpy as np
import sys, os
from scipy.signal import hilbert, butter, filtfilt
import matplotlib.pyplot as plt
from datetime import datetime
from multiprocessing import Pool


def proc(fn):
    string_t = h5py.string_dtype(encoding='ascii')

    fd = h5py.File(fn, 'a')
    nd = -1*np.ones(fd["raw"]["rx0"].shape[1])

    twtt_bed = fd["drv"]["pick"].require_dataset("twtt_bed", shape=nd.shape, data=nd, dtype=np.float32)
    twtt_bed.attrs.create("unit", "second", dtype=string_t)

    description_attr = "Interpreted two way travel time to the bed in each trace in seconds. There are two no data values: -1 indicates that the data has not been interpreted, -9 indicates that the data has been interpreted and there is no observed bed return."
    twtt_bed.attrs.create("description", description_attr, dtype=string_t)

    thick = fd["drv"]["pick"].require_dataset("thick", shape=nd.shape, data=nd, dtype=np.float32)
    thick.attrs.create("unit", "meter", dtype=string_t)

    description_attr = "Thickness of the glacier in meters, calculated using the two way travel times to the surface and bed: thick = (c/sqrt(3.15))*((twtt_surf - twtt_bed)/2) where c = 299792458 m/s. The no data values are the same as the twtt_bed no data values."
    thick.attrs.create("description", description_attr)
    
    fd.close()

def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program for adding twtt_bed and thick DS to hdf5 files"
    )
    parser.add_argument("data", help="Data file(s)", nargs="+")
    parser.add_argument(
        "-n",
        "--num-proc",
        type=int,
        help="Number of simultaneous processes, default 1",
        default=1,
    )
    args = parser.parse_args()

    p = Pool(args.num_proc)
    p.map(proc, args.data)
    p.close()
    p.join()

    return 0


if __name__ == "__main__":
    main()
