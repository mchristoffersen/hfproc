# HDF5 builder - takes in dd dict and filename
import h5py
import numpy as np
from ddVerify import ddVerify
import logging

def generateChirp(cf, bw, length, fs):
  if(cf == -1 or bw == -1 or length == -1 or fs == -1):
    return [0]

  initFreq = cf - (cf*bw/200)
  freqSlope = (cf*bw/100)/length
  nsamp = int(length*fs)
  t = np.linspace(0, length-1.0/fs, nsamp)

  c = np.zeros((nsamp,1))
  for i in range(nsamp):
    c[i] = np.cos(-np.pi/2 + 2*np.pi*(initFreq + (freqSlope/2)*t[i])*t[i])

  return c

def h5build(dd, outf):
  # Verify data dictionary contents
  if(ddVerify(dd)):
    print("Invalid data dictionary, unable to convert to hdf5")
    return 1

  fd = h5py.File(outf, "w")

  # Create group structure
  # |-raw
  # |-drv
  # |  |-pick
  # |-ext

  raw = fd.create_group("raw") 
  drv = fd.create_group("drv")
  drv.create_group("pick")
  fd.create_group("ext")

  # Root attrs
  fd.attrs.create("institution", np.string_("University of Arizona"))
  fd.attrs.create("instrument", np.string_("Arizona Radio-Echo Sounder (ARES)"))


  # rx0 dataset
  rx0 = raw.create_dataset("rx0", data = dd["rx0"], dtype=np.float32, compression="gzip", compression_opts=9, shuffle=True, fletcher32=True)
  rx0.attrs.create("samplingFrequency", dd["fs"], dtype=np.uint64)
  rx0.attrs.create("traceLength", dd["trlen"], dtype=np.float64)
  rx0.attrs.create("stacking", dd["stack"], dtype=np.uint64)
  rx0.attrs.create("samplesPerTrace", dd["spt"], dtype=np.uint64)
  rx0.attrs.create("numTrace", dd["ntrace"], dtype=np.uint64)

  if(dd["sig"] == "chirp"):
    # ref chirp
    chirp = generateChirp(dd["txCF"], dd["txBW"], dd["txlen"], dd["fs"])
    ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
    ch[0:len(chirp)] = chirp

    # tx0 dataset
    tx0 = raw.create_dataset("tx0", data = ch, dtype=np.float32)
    tx0.attrs.create("signal", np.string_("chirp"))
    tx0.attrs.create("centerFrequency", dd["txCF"], dtype=np.float64)
    tx0.attrs.create("bandwidth", dd["txBW"], dtype=np.float64)
    tx0.attrs.create("length", dd["txlen"], dtype=np.float64)
    tx0.attrs.create("pulseRepetitionFrequency", dd["txPRF"], dtype=np.float64)

  elif(dd["sig"] == "tone"):
    # ref tone
    tone = generateChirp(dd["txCF"], 0, dd["txlen"], dd["fs"])
    ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
    ch[0:len(tone)] = tone

    # tx0 dataset
    tx0 = raw.create_dataset("tx0", data = ch, dtype=np.float32)
    tx0.attrs.create("signal", np.string_("tone"))
    tx0.attrs.create("centerFrequency", dd["txCF"], dtype=np.float64)
    tx0.attrs.create("length", dd["txlen"], dtype=np.float64)
    tx0.attrs.create("pulseRepetitionFrequency", dd["txPRF"], dtype=np.float64)

  elif(dd["sig"] == "impulse"):
    # ref impulse, zeros for now
    #tone = generateChirp(dd["txCF"], 0, dd["txlen"], dd["fs"])
    ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
    #ch[0:len(tone)] = tone

    # tx0 dataset
    tx0 = raw.create_dataset("tx0", data = ch, dtype=np.float32)
    tx0.attrs.create("signal", np.string_("impulse"))
    tx0.attrs.create("centerFrequency", dd["txCF"], dtype=np.float64)
    tx0.attrs.create("pulseRepetitionFrequency", dd["txPRF"], dtype=np.float64)

  else:
    print("Unknown signal type")
    sys.exit()

  # loc dataset
  loc_t = np.dtype([('lat', np.float32),
                    ('lon', np.float32),
                    ('altM', np.float32)])
  locList = [None]*dd["ntrace"]
  for i in range(dd["ntrace"]):
    locList[i] = (dd["lat"][i], dd["lon"][i], dd["alt"][i])

  locList = np.array(locList, dtype=loc_t)
  loc0 = raw.create_dataset("loc0", data=locList, dtype=loc_t)
  loc0.attrs.create("CRS", np.string_("WGS84"))

  # time dataset 
  time_t = np.dtype([('fullS', np.uint64),
                     ('fracS', np.float64)])
  timeList = [None]*dd["ntrace"]
  for i in range(dd["ntrace"]):
    timeList[i] = (dd["tfull"][i], dd["tfrac"][i])
  timeList = np.array(timeList, dtype=time_t)
  time0 = raw.create_dataset("time0", data=timeList, dtype=time_t)
  time0.attrs.create("unit", np.string_("second"))
  time0.attrs.create("clock", np.string_("UTC seconds since midnight on 1 Jan 1970"))

  fd.close()

  return 0
