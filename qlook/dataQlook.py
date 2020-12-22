import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import argparse
import logging as log
from multiprocessing import Pool

def saveImage(data, fs, name):
  tbnd = 20e-6 # 20 microseconds
  data = data[0:int(fs*tbnd),:]
  fig = plt.figure(frameon=False)
  ar = .125
  fig.set_size_inches(data.shape[1]/1000/ar, data.shape[0]/1000)
  ax = plt.Axes(fig, [0., 0., 1., 1.])
  ax.set_axis_off()
  fig.add_axes(ax)
  data = np.abs(data) + sys.float_info.epsilon
  im = np.log(data**2)
  ax.imshow(im, aspect=ar, cmap='Greys_r', vmin=np.percentile(im, 60), vmax=np.percentile(im,99.5))
  fig.savefig(name, dpi=500)
  plt.close()

  return 0

def genQlook(fname, outd):
  f = h5py.File(fname, 'r')
  proc0 = f["drv"]["proc0"][:]
  try:
    clutter0 = f["drv"]["clutter0"][:]
  except:
    log.warning("No /drv/clutter0 in " + os.path.basename(fname))

  fs = f["raw"]["rx0"].attrs["samplingFrequency"]
  if(proc0.shape[1] < 20):
    exit()
  saveImage(proc0, fs, outd + '/' + fname.split('/')[-1].replace(".h5", ".png"))
  saveImage(clutter0, fs, outd + '/' + fname.split('/')[-1].replace(".h5", "_clutter.png"))
  f.close()

  return 0

def main():
  # Set up CLI
  parser = argparse.ArgumentParser(description="Program creating quicklook images of /drv/proc0")
  parser.add_argument("outd", help="Output directory")
  parser.add_argument("data", help="Data file(s)", nargs='+')
  parser.add_argument("-n", "--num-proc", type=int, help="Number of simultaneous processes, default 1", default=1)
  args = parser.parse_args()

  # Set up logging - stick in directory with first data file
  log.basicConfig(filename= os.path.dirname(args.outd) + "/genDataQlook.log",
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
  outd = [args.outd]*len(args.data)

  p = Pool(args.num_proc)
  p.starmap(genQlook, zip(args.data, outd))
  p.close()
  p.join()

main()

