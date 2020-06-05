import h5py
import numpy as np
import sys
from scipy.signal import hilbert
import matplotlib.pyplot as plt

def pulseCompress(rx0, refchirp):
  if(len(rx0.shape) == 1):
    rx0 = np.expand_dims(rx0, 1)

  pc = np.zeros(rx0.shape).astype("float32")
  refchirp = np.append(refchirp, np.zeros(len(rx0) - len(refchirp)))
  C = np.conj(np.fft.fft(refchirp))
  PC = np.fft.fft(rx0, axis=0)
  PC = PC*C[:,None]
  pc = np.fft.ifft(PC, axis=0)

  return pc

def removeSlidingMeanFFT(rx0, sumint):
  # Sumint in interval to avg over for mean removal
  mean = np.zeros(rx0.shape)
  a = np.zeros(rx0.shape[1])
  a[0:sumint//2] = 1
  a[rx0.shape[1]-sumint//2:rx0.shape[1]] = 1
  A = np.fft.fft(a)

  # Main circular convolution
  for i in range(rx0.shape[0]):
    T = np.fft.fft(rx0[i,:])
    mean[i,:] = np.real(np.fft.ifft(np.multiply(T,A))/sumint)

  # Handle edges
  mt = np.zeros(rx0.shape[0])
  for i in range(0, sumint):
    mt = np.add(mt, np.divide(rx0[:,i], sumint))

  for i in range(0, sumint//2):
    mean[:,i] = mt

  mt = np.zeros(rx0.shape[0])
  for i in range(rx0.shape[1] - sumint, rx0.shape[1]):
    mt = np.add(mt, np.divide(rx0[:,i], sumint))

  for i in range(rx0.shape[1] - sumint//2, rx0.shape[1]):
    mean[:,i] = mt

  rx0NM = np.subtract(rx0, mean)

  return rx0NM

def removeSlidingMean(rx0):
  sumint = 50
  rx0NM = np.zeros(rx0.shape)

  for i in range(rx0.shape[1]): 
    mt = np.zeros(rx0.shape[0])

    if(i < sumint/2):
      for j in range(0, sumint):
        mt = np.add(mt, np.divide(rx0[:,j], sumint))
      rx0NM[:,i] = mt #rx0[:,i] - mt


    elif(i > rx0.shape[1] - sumint//2):
      for j in range(rx0.shape[1] - sumint, rx0.shape[1]):
        mt = np.add(mt, np.divide(rx0[:,j], sumint))
      rx0NM[:,i] = mt #rx0[:,i] - mt

    else:
      for j in range(i-sumint//2, i+sumint//2):
        mt = np.add(mt, np.divide(rx0[:,j], sumint))
      rx0NM[:,i] = mt #rx0[:,i] - mt

  return rx0NM

def removeMean(rx0):
  rx0NM = np.zeros(rx0.shape)
  mt = np.zeros(rx0.shape[0])

  for i in range(rx0.shape[1]): 
    mt = np.add(mt, np.divide(rx0[:,i], rx0.shape[1]))

  for i in range(rx0.shape[1]): 
    rx0NM[:,i] = rx0[:,i] - mt

  return rx0NM

def arangeN(nsamp,fs):
    # Generate an nsamp length array with samples at fs frequency
    seq = np.zeros(nsamp).astype(np.double)
    c = 0
    
    for i in range(nsamp):
        seq[i] = c
        c += 1.0/fs
    
    return seq

def arangeT(start, stop, fs):
    # Function to generate set of 
    # Args are start time, stop time, sampling frequency
    # Generates times within the closed interval [start, stop] at 1/fs spacing
    # Double precision floating point
    
    # Slow way to do this, but probably fine for the homework
    seq = np.array([]).astype(np.double)
    c = start
    while c <= stop:
        seq = np.append(seq,c)
        c += 1.0/fs
        
    return seq

def baseChirp(tlen, cf, bw, fs):
    # Function to generate a linear basebanded chirp
    # Amplitude of 1, flat window
    
    i = np.complex(0,1)
    t = arangeT(0,tlen,fs)
    fstart = -(.5 * cf * bw)
    b = (cf * bw)/tlen

    c = np.exp(2*np.pi*i*(.5*b*np.square(t) + fstart*t))

    return c

def findOffset(rx0, tlen, cf, bw, fs):
  # Make chirp that is second half of real chirp
  tlen = tlen/2
  endf = cf + (.5*cf*bw)
  startf = cf
  cf = (startf+endf)/2
  bw = (endf-startf)/cf
  refchirp = baseChirp(tlen, cf, bw, fs)

  # Baseband data to cf of new chirp
  rx0 = baseband(rx0, cf, fs)

  # Cross correlate with avg of first 10 traces, get peak loc
  rxAvg = np.mean(rx0[:,0:10], axis=1)
  pkLoc = np.argmax(pulseCompress(rxAvg, refchirp))

  return int(pkLoc - (tlen*fs))

def baseband(sig, cf, fs):
  # Baseband traces to the frequency cf
  i = np.complex(0,1)
  t = arangeN(sig.shape[0], fs)
  fb = np.exp(2*np.pi*i*-cf*t)

  if(len(sig.shape) > 1 and max(sig.shape) > 1):
    sig = sig * fb[:, None]
  else:
    sig = sig * fb

  return sig

def main():
  f = h5py.File(sys.argv[1], 'r+')

  rx0 = f["raw"]["rx0"][:]
  cf = f["raw"]["tx0"].attrs["chirpCenterFrequency-Hz"]
  bw = f["raw"]["tx0"].attrs["chirpBandwidth-Pct"]
  tl = f["raw"]["tx0"].attrs["chirpLength-S"]
  fs = f["raw"]["rx0"].attrs["samplingFrequency-Hz"]

  ### Process data
  # Find hardware delay with outgoing wave
  shift = findOffset(rx0, tl, cf, bw, fs)
  # Circular shift to correct for hardware delay
  rx0 = np.roll(rx0, -shift, axis=0)

  avgw = 250
  if(rx0.shape[1] > avgw):
    rx0 = removeSlidingMeanFFT(rx0, avgw)
  else:
    rx0 = removeMean(rx0)

  rx0 = hilbert(rx0, axis=0)
  rx0 = baseband(rx0, cf, fs)
  refchirp = baseChirp(tl, cf, bw, fs)
  pc = pulseCompress(rx0, refchirp)

  # Save processed dataset
  proc0 = f["drv"].require_dataset("proc0", shape=pc.shape, dtype=np.complex64, compression="gzip", compression_opts=9, shuffle=True, fletcher32=True)
  proc0[:] = pc.astype(np.complex64)
  proc0.attrs.create("RefChirp", np.string_("/raw/tx0"))
  proc0.attrs.create("Notes", np.string_("Mean removed in sliding {} trace window".format(avgw)))
  f.close()
  print(sys.argv[1])

main()
