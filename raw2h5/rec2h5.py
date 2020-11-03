import sys, h5py, scipy.io
import numpy as np
import scipy.signal as spsig
import scipy.stats as spstat
import matplotlib.pyplot as plt
from h5build import h5build
from datetime import datetime, timedelta
import os.path
import pandas as pd

def findOffsetDT(rx0):
  # Find offset with time derivative. 
  # Get mean trace
  mt = np.mean(rx0, axis=1)

  # Gradient
  dmt = np.gradient(mt)

  # Standard deviation
  std = np.std(dmt)

  # Find first place with slope > 1 std dev
  pkLoc = np.argmax(np.abs(dmt) > std)

  return pkLoc


def parseRaw(fname):
  dd = {}

  fd = scipy.io.loadmat(fname)

  # Open matching signal info file and get info
  year = fname.split("/")[-1][0:4]
  cols = ["name", "sig", "cf", "bw", "len"]
  df = pd.read_csv(os.path.dirname(fname) + "/" + year + "meta.csv", names=cols)
  name = os.path.basename(fname).replace(".mat", "")
  nfo = df[df["name"] == name].reset_index()
  if(len(nfo) != 1):
    print("Invalid metadata match:\n\t" + fname)
    return -1

  # Ingest data from rec struct
  ch0 = fd["rec"]["ch0"][0][0]
  lat = fd["rec"]["lat"][0][0][0]
  lon = fd["rec"]["lon"][0][0][0]
  elev = fd["rec"]["ele"][0][0][0]
  time = fd["rec"]["time"][0][0][0]
  time = pd.to_datetime(time-719529, unit='D') # Convert matlab to unix epoch
  dt = fd["rec"]["dt"][0][0][0][0]

  dd["rx0"] = np.transpose(ch0).astype(np.float32)
    
  dd["ntrace"] = dd["rx0"].shape[1]

  dd["lat"] = lat.astype(np.float32)
  dd["lon"] = lon.astype(np.float32)
  dd["alt"] = elev.astype(np.float32)

  dd["tfull"] = np.zeros(dd["ntrace"]).astype(np.uint64)
  dd["tfrac"] = np.zeros(dd["ntrace"]).astype(np.float64)

  dd["sig"] = nfo["sig"][0]

  if(dd["sig"] == "chirp"):
    dd["txCF"] = nfo["cf"][0]
    dd["txBW"] = nfo["bw"][0]/100.0
    dd["txlen"] = nfo["len"][0]
    dd["txPRF"] = -1
  elif(dd["sig"] == "tone"):
    dd["txCF"] = nfo["cf"][0]
    dd["txlen"] = -1
    dd["txPRF"] = -1
  elif(dd["sig"] == "impulse"):
    dd["txCF"] = -1
    dd["txPRF"] = -1

  dd["fs"] = 1.0/dt
  dd["stack"] = -1
  dd["spt"] = dd["rx0"].shape[0]
  dd["trlen"] = dt * dd["spt"]

  # Deal with duplicate times
  timen = np.zeros(len(time))
  for i in range(dd["ntrace"]):
    timen[i] = time[i].value/10e8 - 37 #TAI to UTC

  uniq, idx = np.unique(timen, return_index=True)
  x = np.array(range(len(timen)))
  timen = np.interp(x, idx, uniq)

  for i in range(dd["ntrace"]):
    dd["tfull"][i] = int(timen[i])
    dd["tfrac"][i] = timen[i] - int(timen[i])

  # Handle offset changes over 2015, 2016, 2017 campaigns
  fn = sys.argv[1].split('/')[-1]
  date = datetime.strptime(fn, '%Y%m%d-%H%M%S.mat')

  # 2015 - May
  if(date.year == 2015 and date.month == 5):
    if(dd["sig"] == "impulse"):
      if(date.day <= 17):
        dd["rx0"] = np.roll(dd["rx0"], -347, axis=0)
      elif(date.day == 19 and date.hour == 22 and date.minute <= 34):
        dd["rx0"] = np.roll(dd["rx0"], -147, axis=0)
      else:
        dd["rx0"] = np.roll(dd["rx0"], -172, axis=0)
    elif(dd["sig"] == "chirp"):
      dd["rx0"] = np.roll(dd["rx0"], -537, axis=0)

  # 2015 Aug
  elif(date.year == 2015 and date.month == 8):
    if(dd["sig"] == "impulse"):
      dd["rx0"] = np.roll(dd["rx0"], -347, axis=0)
    elif(dd["sig"] == "chirp"):
      dd["rx0"] = np.roll(dd["rx0"], -393, axis=0)

  # 2016 May
  elif(date.year == 2016 and date.month == 5):
    if(dd["sig"] == "impulse"):
      ofst = findOffsetDT(dd["rx0"])
      dd["rx0"] = np.roll(dd["rx0"], -ofst, axis=0)
    elif(dd["sig"] == "chirp"):
      # This won't work for a few, need to get more granular
      dd["rx0"] = np.roll(dd["rx0"], -570, axis=0)

  # 2016 Aug
  elif(date.year == 2016 and date.month == 8):
    if(dd["sig"] == "impulse"):
      dd["rx0"] = np.roll(dd["rx0"], -325, axis=0)
    elif(dd["sig"] == "chirp"):
      # This won't work for a few, need to get more granular
      dd["rx0"] = np.roll(dd["rx0"], -565, axis=0)

  #2017 May
  elif(date.year == 2017 and date.month == 5):
    dd["rx0"] = np.roll(dd["rx0"], -571, axis=0)

  elif(date.year == 2017 and date.month == 8):
    if(date.day <= 16):
      dd["rx0"] = np.roll(dd["rx0"], -370, axis=0)
    elif(date.day == 22):
      dd["rx0"] = np.roll(dd["rx0"], -477, axis=0)
    elif(date.day > 22):
      dd["rx0"] = np.roll(dd["rx0"], -364, axis=0)

  else:
    print("NO OFFSET CORRECTION FOUND\n\t" + fn)
    exit()



  return dd
  

def main():
  dd = parseRaw(sys.argv[1])
  outf = sys.argv[2] + '/' + sys.argv[1].split('/')[-1].replace(".mat",".h5")
  print(outf)
  if(dd == -1):
    exit()

  # Open file
  fd = h5py.File(outf, "w")

  h5build(dd, fd)

  # Some basic info at file root
  #fd.attrs.create("Info", np.string_("Data acquired by the University of Texas Very Efficient Radar Very Efficient Team (VERVET) radar system"))
  fd.close()

main()
