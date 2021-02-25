import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import argparse

# Add appropriate surface data to hdf5 file

def main():
  # Set up CLI
  parser = argparse.ArgumentParser(
    description="Program for adding surface info to hdf5 files"
  )
  parser.add_argument("srf", help="Surface info files", nargs="+")
  parser.add_argument("data", help="Data file(s)", nargs="+")
  args = parser.parse_args()

  # Sort nav and data
  srf = []
  data = []
  for f in args.srf + args.data:
    if f.split('.')[-1] == "csv":
      srf.append(f)
    elif f.split('.')[-1] == "h5":
      data.append(f)
    else:
      print("Unknown file type:", f)

  for data in data:
    countf = data.replace("/hdf5/", "/srf/").replace(".h5", "_count.csv")
    srff = data.replace("/hdf5/", "/srf/").replace(".h5", "_srf.csv")

    try:
      f = h5py.File(data, "a")
      count = np.loadtxt(countf)
      srf = np.loadtxt(srff)
    except Exception as e:
      f.close()
      print("Error reading file")
      print(e)
      continue

    if(srf.shape == ()):
        print("Empty surface")
        f.close()
        continue

    srf0 = f["ext"].require_dataset("srf0", shape=srf.shape, data=srf, dtype=np.float32)
    srf0[:] = srf[:]
    srf0.attrs.create("unit", np.string_("meter"))
    srf0.attrs.create("verticalDatum", np.string_("WGS84 Ellipsoid"))

    srf0count = f["ext"].require_dataset("srf0count", shape=count.shape, data=count, dtype=np.uint32)
    srf0count[:] = count[:]

    # Add in twtt_surf dataset
    c = 299792458  # Speed of light at STP

    elev_air = f["ext"]["nav0"]["hgt"][:]

    twtt_surf = 2 * (elev_air - srf) / c

    twtt_surf[srf == -9999] = -1

    twtt_surf_pick = f["drv"]["pick"].require_dataset(
        "twtt_surf", data=twtt_surf, shape=twtt_surf.shape, dtype=np.float32
    )
    twtt_surf_pick[:] = twtt_surf[:]

    twtt_surf_pick.attrs.create("unit", np.string_("second"))
    print(data, "WORKED")
    f.close()


main()
