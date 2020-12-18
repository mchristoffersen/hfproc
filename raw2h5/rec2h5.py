import sys, h5py, scipy.io
import numpy as np
import scipy.signal as spsig
import scipy.stats as spstat
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os.path
import pandas as pd
import logging as log

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
  fn = fname.split('/')[-1]

  try:
    fd = scipy.io.loadmat(fname)
  except:
    log.warning("Failed to load mat file " + fn)
    return -1

  log.debug("Loaded mat file " + fn)

  # Open matching signal info file and get info
  year = fname.split("/")[-1][0:4]
  cols = ["name", "sig", "cf", "bw", "len"]
  meta = os.path.dirname(fname) + "/" + year + "meta.csv"
  if(not os.path.isfile(meta)):
    log.warning("Metadata file does not exist " + meta)

  df = pd.read_csv(meta, names=cols)
  log.debug("Loaded metadata file " + meta)
  name = os.path.basename(fname).replace(".mat", "")
  nfo = df[df["name"] == name].reset_index()
  if(len(nfo) != 1):
    log.warning("Can't find metadata for " + fn)
    return -1

  log.debug("Applied metadata from " + meta)

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
  log.warning("No TAI to UTC conversion " + fn)
  for i in range(dd["ntrace"]):
    timen[i] = time[i].value/10e8 #- 37 #TAI to UTC

  uniq, idx = np.unique(timen, return_index=True)
  x = np.array(range(len(timen)))
  timen = np.interp(x, idx, uniq)

  for i in range(dd["ntrace"]):
    dd["tfull"][i] = int(timen[i])
    dd["tfrac"][i] = timen[i] - int(timen[i])

  # Handle offset changes over 2015, 2016, 2017 campaigns
  date = datetime.utcfromtimestamp(dd["tfull"][0])
  ofcorr = np.nan
  # 2013 - not sure if this is totally right
  if(date.year == 2013):
    ofcorr = -285

  # 2014 May
  if(date.year == 2014 and date.month == 5):
    ofcorr = -295

  # 2014 Aug
  if(date.year == 2014 and date.month == 8):
    ofcorr = -396

  # 2015 May
  if(date.year == 2015 and date.month == 5):
    if(dd["sig"] == "impulse"):
      if(date.day <= 17):
        ofcorr = -347
      elif(date.day == 19 and date.hour == 22 and date.minute <= 34):
        ofcorr = -147
      else:
        ofcorr = -172
    elif(dd["sig"] == "chirp"):
      ofcorr = -537

  # 2015 Aug
  elif(date.year == 2015 and date.month == 8):
    if(dd["sig"] == "impulse"):
      ofcorr = -347
    elif(dd["sig"] == "chirp"):
      ofcorr = -393

  # 2016 May
  elif(date.year == 2016 and date.month == 5):
    if(dd["sig"] == "impulse"):
      ofst = findOffsetDT(dd["rx0"])
      ofcorr = -ofst
    elif(dd["sig"] == "chirp"):
      # This won't work for a few, need to get more granular
      ofcorr = -570

  # 2016 Aug
  elif(date.year == 2016 and date.month == 8):
    if(dd["sig"] == "impulse"):
      ofcorr = -325
    elif(dd["sig"] == "chirp"):
      # This won't work for a few, need to get more granular
      ofcorr = -565

  #2017 May
  elif(date.year == 2017 and date.month == 5):
    ofcorr = -571

  elif(date.year == 2017 and date.month == 8):
    if(date.day <= 16):
      ofcorr = -370
    elif(date.day == 22):
      ofcorr = -477
    elif(date.day > 22):
      ofcorr = -364

  if(not np.isnan(ofcorr)):
    dd["rx0"] = np.roll(dd["rx0"], ofcorr, axis=0)
  else:
    log.warning("No offset correction found for " + fn)

  return dd
