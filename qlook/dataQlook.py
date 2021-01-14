import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import argparse
import logging as log
from multiprocessing import Pool


def saveImage(data, fs, name):
    tbnd = 20e-6  # 20 microseconds
    data = data[0 : int(fs * tbnd), :]
    fig = plt.figure(frameon=False)
    ar = 0.125
    fig.set_size_inches(data.shape[1] / 1000 / ar, data.shape[0] / 1000)
    ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
    ax.set_axis_off()
    fig.add_axes(ax)
    data = np.abs(data) + sys.float_info.epsilon
    im = np.log(data ** 2)
    ax.imshow(
        im,
        aspect=ar,
        cmap="Greys_r",
        vmin=np.percentile(im, 60),
        vmax=np.percentile(im, 99.5),
    )
    fig.savefig(name, dpi=500)
    plt.close()

    return 0


def genQlook(fname, outd):
    fd = h5py.File(fname, "r")

    fs = fd["raw"]["rx0"].attrs["samplingFrequency"]

    try:
        proc0 = fd["drv"]["proc0"][:]
        saveImage(proc0, fs, outd + "/" + fname.split("/")[-1].replace(".h5", ".png"))
    except Exception as e:
        log.error("Error generating data qlook " + os.path.basename(fname))
        log.error(e)

    try:
        clutter0 = fd["drv"]["clutter0"][:]
        saveImage(
            clutter0,
            fs,
            outd + "/" + fname.split("/")[-1].replace(".h5", "_clutter.png"),
        )
    except Exception as e:
        log.error("Error generating clutter qlook " + os.path.basename(fname))
        log.error(e)

    fd.close()

    return 0


def main():
  # Set up CLI
  parser = argparse.ArgumentParser(description="Program creating quicklook images of /drv/proc0")
  parser.add_argument("dest", help="Output directory")
  parser.add_argument("data", help="Data file(s)", nargs='+')
  parser.add_argument("-n", "--num-proc", type=int, help="Number of simultaneous processes, default 1", default=1)
  args = parser.parse_args()

  # Set up logging - stick in directory with first data file
  log.basicConfig(filename= os.path.dirname(args.dest) + "/genDataQlook.log",
                  format='%(levelname)s:%(process)d:%(message)s    %(asctime)s',
                  level=log.INFO)

  # Print warning and error to stderr
  sh = log.StreamHandler()
  sh.setLevel(log.WARNING)
  sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
  log.getLogger('').addHandler(sh)

  log.info("Starting data and clutter quicklook generation")
  log.info("num_proc %s", args.num_proc)
  log.info("dest %s", args.dest)
  log.info("data %s", args.data)

  #Do conversion
  outd = [args.dest]*len(args.data)

  p = Pool(args.num_proc)
  p.starmap(genQlook, zip(args.data, outd))
  p.close()
  p.join()

    # Set up logging - stick in directory with first data file
    log.basicConfig(
        filename=os.path.dirname(args.dest) + "/genDataQlook.log",
        format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
        level=log.INFO,
    )

    # Print warning and error to stderr
    sh = log.StreamHandler()
    sh.setLevel(log.WARNING)
    sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
    log.getLogger("").addHandler(sh)

    log.info("Starting data and clutter quicklook generation")
    log.info("num_proc %s", args.num_proc)
    log.info("dest %s", args.dest)
    log.info("data %s", args.data)

    # Do conversion
    dest = [args.dest] * len(args.data)

    p = Pool(args.num_proc)
    p.starmap(genQlook, zip(args.data, dest))
    p.close()
    p.join()


main()
