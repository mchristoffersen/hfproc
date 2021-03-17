import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import argparse

# Add appropriate clutter sim to hdf5 file
# Adjust sim sampling to match radar



def main():
  # Set up CLI
  parser = argparse.ArgumentParser(
    description="Program for rolling mean removal and pulse compression of HDF5 files"
  )
  parser.add_argument("sims", help="Combined binary sim file(s)", nargs="+")
  parser.add_argument("data", help="Data file(s)", nargs="+")
  args = parser.parse_args()

  # Sort nav and data
  sims = []
  data = []
  for f in args.sims + args.data:
    if f.split('.')[-1] == "img":
      sims.append(f)
    elif f.split('.')[-1] == "h5":
      data.append(f)
    else:
      print("Unknown file type:", f)

  for sim in sims:
    simid = sim.split("/")[-1].replace("_combined.img","")
    h5 = sim.replace("/sim/", "/hdf5/").replace("_combined.img",".h5")

    try:
      f = h5py.File(h5, "a")
      spt = f["raw"]["rx0"].attrs["samplesPerTrace"]
      ntrace = f["raw"]["rx0"].attrs["numTrace"]
      fs = f["raw"]["rx0"].attrs["samplingFrequency"]
      sim = np.fromfile(sim, dtype=np.float32)
    except Exception as e:
      f.close()
      print("Error reading file " + h5)
      print(e)
      return 1

    out = sim.reshape((5000, ntrace))

    if fs != 100e6:
      # Handle 50 MHz data by summing neighboring samples
      if fs == 50e6:
        out = out + np.roll(out, -1, axis=0)
        out = out[::2, :]
      # Handle 200 MHz data by duplicating samples
      elif fs == 200e6:
        out = np.repeat(out, 2, axis=0)
      else:
        print("New fs")
        sys.exit(1)

    # Handle short sim with zero pad
    if out.shape[0] < spt:
      out = np.append(out, np.zeros((int(spt - out.shape[0]), out.shape[1])), axis=0)

    # Handle long sim by truncation
    if out.shape[0] > spt:
      out = out[:spt, :]

    clutter0 = f["drv"].require_dataset(
        "clutter0",
        data=out.astype(np.float32),
        shape=out.shape,
        dtype=np.float32,
        compression="gzip",
        compression_opts=9,
        shuffle=True,
        fletcher32=True,
    )

    string_t = h5py.string_dtype(encoding='ascii')
    description_attr = "Surface clutter simulation to aid interpretation of the data."
    clutter0.attrs.create("description", description_attr, dtype=string_t)
    
    clutter0[:] = data=out.astype(np.float32)[:]
    f.close()


main()
