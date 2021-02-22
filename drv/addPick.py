import logging as log, sys, argparse, os
import h5py
import numpy as np
import sys, os
from scipy.signal import hilbert, butter, filtfilt
import matplotlib.pyplot as plt
from datetime import datetime
from multiprocessing import Pool


def proc(fn):
    fd = h5py.File(fn, 'a')
    nd = -1*np.ones(fd["raw"]["rx0"].shape[1])

    twtt_bed = fd["drv"]["pick"].require_dataset("twtt_bed", shape=nd.shape, data=nd, dtype=np.float32)
    twtt_bed.attrs.create("unit", np.string_("second"))

    thick = fd["drv"]["pick"].require_dataset("thick", shape=nd.shape, data=nd, dtype=np.float32)
    thick.attrs.create("unit", np.string_("meter"))

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
