import h5py
import numpy as np
import sys
import matplotlib.pyplot as plt
import scipy.signal

def filter(pc):
  # Low pass in slow time
  #[b, a] = scipy.signal.butter(4, .1, btype='lowpass', fs=20)
  #pc = scipy.signal.filtfilt(b, a, pc, axis=1)

  # Low pass in fast time
  [b, a] = scipy.signal.butter(4, 1e6, btype='lowpass', fs=100e6)
  pc = scipy.signal.filtfilt(b, a, pc, axis=0)

  # Plot filter response
  #[w, h] = scipy.signal.freqz(b, a=a, fs=20)
  #plt.plot(w, 20*np.log10(abs(h)))
  #plt.show()
  return pc

def fftplot(pc):
  # Plot slow time FFTs as an image
  PC = np.fft.fft(pc, axis=1)
  PC = np.fft.fftshift(PC, axes=(1))
  frq = np.fft.fftfreq(PC.shape[1], d=1.0/20)
  plt.imshow(np.log(np.abs(PC)), extent=[-10, 10, 0, PC.shape[0]], aspect="auto")
  plt.show()

def main():
  f = h5py.File(sys.argv[1], 'a')
  proc0 = f["drv"]["proc0"][:]
  proc0 = filter(proc0)
  f["drv"]["proc0"][:] = proc0
  f["drv"]["proc0"].attrs.create("Filter", np.string_("4th Order 1 MHz low-pass Butterworth"))
  f.close()

main()
