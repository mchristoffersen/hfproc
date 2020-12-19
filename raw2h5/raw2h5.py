import logging as log, sys, argparse
from multiprocessing import Pool
import rec2h5, tdms2h5, lowres2h5
from h5build import h5build
from datetime import datetime
import matplotlib.pyplot as plt

# Wrapper for raw data to HDF5 transformation
def convert(fname, ftype, dest):
  xfd = {"rec":rec2h5, "tdms":tdms2h5, "lowres":lowres2h5}
  xf = xfd[ftype]
  log.info("Parsing " + fname)
  dd = xf.parseRaw(fname)

  fshort = fname.split('/')[-1]

  if(dd == -1):
    log.error("Invalid %s data file %s", ftype, fname)
    return 1

  log.info("Created data dict " + fname.split('/')[-1])
  log.info("File info (signal,%s) (ntrace,%d) %s",
            dd["sig"], dd["ntrace"],
            fname.split('/')[-1])

  date = datetime.utcfromtimestamp(dd["tfull"][0])
  outf = dest + '/' + fshort.replace(".mat", ".h5")
  outfshort = fshort.replace(".mat", ".h5")
  #outf = date.strftime(dest + "/%Y%m%d-%H%M%S.h5")
  #outfshort = outf.split('/')[-1]

  # Build hdf5 file
  log.info("src file %s ---> dst file %s", fshort, outfshort)
  log.info("Building HDF5 file " + outf)

  #plt.imshow(dd["rx0"])
  #plt.show()

  if(h5build(dd, outf)):
    log.error("Unable to convert " + fname.split('/')[-1])

  log.info("Built HDF5 file " + outf.split('/')[-1])

  return 0



def main():
  # Set up CLI
  parser = argparse.ArgumentParser(description="Program for conversion of raw radar sounding files to HDF5")
  parser.add_argument("type", help="File type of raw data file(s)", choices=["rec", "tdms", "lowres"])
  parser.add_argument("dest", help="Destination directory for converted file(s)")
  parser.add_argument("data", help="Raw data file(s)", nargs='+')
  parser.add_argument("-n", "--num-proc", type=int, help="Number of simultaneous processes, default 1", default=1)
  args = parser.parse_args()

  # Set up logging
  log.basicConfig(filename=args.dest + "/raw2h5.log",
                  format='%(levelname)s:%(process)d:%(message)s    %(asctime)s',
                  level=log.INFO)

  # Print warning and error to stderr
  sh = log.StreamHandler()
  sh.setLevel(log.WARNING)
  sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
  log.getLogger('').addHandler(sh)

  log.info("Starting raw to HDF5 conversion")
  log.info("num_proc %s", args.num_proc)
  log.info("type %s", args.type)
  log.info("dest %s", args.dest)
  log.info("data %s", args.data)

  #Do conversion
  ftype = [args.type]*len(args.data)
  dest = [args.dest]*len(args.data)

  p = Pool(args.num_proc)
  p.starmap(convert, zip(args.data, ftype, dest))
  p.close()
  p.join()

  return 0

if __name__ == "__main__":
	main()
