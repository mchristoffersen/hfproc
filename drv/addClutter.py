import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt

"""
add appropriate clutter sim to radar hdf5 dataset
tile sim data if sim was downsampled initially
"""

def main():
  clutterFile = sys.argv[1]
  hdfFile = sys.argv[2] + "/" + clutterFile.split('/')[-1].replace("_combined.img",".h5")
  print(hdfFile)
  f = h5py.File(hdfFile, 'a')
  spt = f["raw"]["rx0"].attrs["samplesPerTrace"]
  ntrace = f["raw"]["rx0"].attrs["numTrace"]
  fs = f["raw"]["rx0"].attrs["samplingFrequency-Hz"]
  sim = np.fromfile(clutterFile,dtype=np.float32)

#  # determine sim downsampling factor
#  factor = int(ntrace*spt)/len(sim)
#  print(factor)
#  if int(factor) != factor:
#
#  if(factor != 1):
#    for i in range(ntrace//factor):
#      # tile sim data to achieve same array size as data
#      out = np.append(out,np.tile(sim[int(i*spt):int((i+1)*spt)],factor))
#
#  else:

  # reshape sim to match 2d radar data
  out = sim.reshape((5000,ntrace))

  # Handle 50 MHz data by summing neighboring samples
  if(fs != 100e6):
    if(fs != 50e6):
      print("New fs")
      sys.exit(1)

    out = out + np.roll(out,-1,axis=0)
    out = out[::2,:]

  # Handle short sim with zero pad
  if(out.shape[0] < spt):
    out = np.append(out, np.zeros((int(spt-out.shape[0]), out.shape[1])), axis=0)

  # Handle long sim by truncation
  if(out.shape[0] > spt):
    out = out[:spt,:]

  clutter0 = f["drv"].require_dataset("clutter0", data=out.astype(np.float32), shape=out.shape, dtype=np.float32, compression="gzip", compression_opts=9, shuffle=True, fletcher32=True)
  f.close()

main()
