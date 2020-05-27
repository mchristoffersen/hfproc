# HDF5 builder - takes in dd dict and filename
import h5py
import numpy as np

def generateChirp(cf, bw, length, fs):
  initFreq = cf - (cf*bw/200)
  freqSlope = (cf*bw/100)/length
  nsamp = int(length*fs)
  t = np.linspace(0, length-1/fs, nsamp)

  c = np.zeros((nsamp,1))
  for i in range(nsamp):
    c[i] = np.cos(-np.pi/2 + 2*np.pi*(initFreq + (freqSlope/2)*t[i])*t[i])

  return c

def h5build(dd, outf):

  # Create group structure
  # |-raw
  # |-drv
  # |  |-pick
  # |-ext

  f = h5py.File(outf, "w")

  raw = f.create_group("raw") 
  drv = f.create_group("drv")
  drv.create_group("pick")
  f.create_group("ext")

  # rx0 dataset
  rx0 = raw.create_dataset("rx0", data = dd["rx0"], dtype=np.float32, compression="gzip", compression_opts=9, shuffle=True, fletcher32=True)
  rx0.attrs.create("samplingFrequency-Hz", dd["fs"], dtype=np.uint64)
  rx0.attrs.create("traceLength-S", dd["traceLen"], dtype=np.float64)
  rx0.attrs.create("stacking", dd["stack"], dtype=np.uint64)
  rx0.attrs.create("samplesPerTrace", dd["spt"], dtype=np.uint64)
  rx0.attrs.create("numTrace", dd["ntrace"], dtype=np.uint64)

  # ref chirp
  chirp = generateChirp(dd["chirpCF"], dd["chirpBW"], dd["chirpLen"], dd["fs"])
  ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
  ch[0:len(chirp)] = chirp

  # tx0 dataset
  tx0 = raw.create_dataset("tx0", data = ch, dtype=np.float32)
  tx0.attrs.create("chirpCenterFrequency-Hz", dd["chirpCF"], dtype=np.float64)
  tx0.attrs.create("chirpBandwidth-Pct", dd["chirpBW"], dtype=np.float64)
  tx0.attrs.create("chirpLength-S", dd["chirpLen"], dtype=np.float64)
  tx0.attrs.create("chirpPulseRepetitionFrequency-Hz", dd["chirpPRF"], dtype=np.float64)

  # loc dataset
  loc_t = np.dtype([('lat', np.float32),
                    ('lon', np.float32),
                    ('altM', np.float32),
                    ('DOP', np.float32),
                    ('nsat', np.uint8)])
  locList = [None]*dd["ntrace"]
  for i in range(dd["ntrace"]):
    locList[i] = (dd["lat"][i], dd["lon"][i], dd["alt"][i], dd["dop"][i], dd["nsat"][i])
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
  time0.attrs.create("Clock", np.string_("GPS"))

  f.close()

  return 0
