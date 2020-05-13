# Turn surface elevation in ext/srf0 and aircraft elevation in ext/nav0 into a
# two way travel time vector that is stored in drv/pick/twtt_surf

import h5py
import numpy as np
import sys

def main():
  print(sys.argv[1])
  c = 299792458 # Speed of light at STP
  f = h5py.File(sys.argv[1], 'a')
  ext = f["ext"]

  # Check if srf0 and nav0 datasets exist, bail if not
  if("srf0" in ext.keys() and "nav0" in ext.keys()):
    elev_surf = ext["srf0"][:]
    elev_air =  ext["nav0"]["altM"][:]

    twtt_surf = 2*(elev_air - elev_surf)/c

    twtt_surf_pick = f["drv"]["pick"].require_dataset("twtt_surf", data=twtt_surf, shape=twtt_surf.shape, dtype=np.float32)
    twtt_surf_pick.attrs.create("Unit", np.string_("Seconds"))
    twtt_surf_pick.attrs.create("Source", np.string_("OIB LIDAR"))
    f.close()

  else:
    f.close()
    print(sys.argv[1] + " surface pick creation failed." + list(ext.keys()[0]))


main()

