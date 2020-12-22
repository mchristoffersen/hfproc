import h5py
import numpy as np
import sys
import matplotlib.pyplot as plt

def saveImage(pc, fs, name):
  tbnd = 20e-6 # 20 microseconds
  pc = pc[0:tbnd//fs,:]
  fig = plt.figure(frameon=False)
  ar = 2
  fig.set_size_inches(pc.shape[1]/1000/ar, pc.shape[0]/1000)
  ax = plt.Axes(fig, [0., 0., 1., 1.])
  ax.set_axis_off()
  fig.add_axes(ax)
  pc = np.abs(pc)
  im = np.log(pc**2)
  ax.imshow(im, aspect=ar, cmap='Greys_r', vmin=.4*np.min(im), vmax=.9*np.max(im))
  fig.savefig(name, dpi=500)

def main():
  f = h5py.File(sys.argv[1], 'r')
  proc0 = f["drv"]["proc0"][:]
  fs = f["raw"]["rx0"].attrs["samplingFrequency"]
  if(proc0.shape[1] < 20):
    exit()
  saveImage(proc0, fs, sys.argv[2] + '/' + sys.argv[1].split('/')[-1].replace(".h5", ".png"))
  f.close()

main()

