import sys, h5py, nptdms
import numpy as np
from h5build import h5build
from datetime import datetime, timedelta
import logging as log

def tdmsSlice(data, spt, bark, spb):
  # Number of samples total
  # Samples per trace
  # Bark (boolean)
  # Samples per bark
  # Returns ch0 chirp data
  if(int(spt) != spt or int(spb) != spb):
    print("Non-integer spt or spb in tdms slice")
    sys.exit()
    
  spt = int(spt)
  spb = int(spb)
    
  ntrace = len(data)/spt
  
  if(int(ntrace) != ntrace):
    print("TDMS slicing error")
    sys.exit()
    
  ntrace = int(ntrace)
  rx0 = np.reshape(data, (spt,ntrace), order='F')
  
  # Spt contains spb. Chirp data len is spt-spb
  rx0 = rx0[spb*bark:,:]
  
  return rx0
  
  
def parseRaw(fname):
  dd = {}

  fd = nptdms.TdmsFile(fname)

  try:
    fd["meta"]
  except:
    sys.stdout.write("No meta object, skipping: ")
    return -1

  ch0 = fd["radar"]["ch0"]  #.channel_data("radar","ch0")
  lat = fd["meta"]["lat"]
  lon = fd["meta"]["lon"]
  elev = fd["meta"]["elev"]
  time = fd["meta"]["time"]
  root = fd.properties
  
  startTime = root["start_time"]
  startTime = datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%S.%f")

  dd["sig"] = "chirp" # All TDMS files are chirped

  dd["txCF"] = root["chirp_cf"]
  dd["txBW"] = root["chirp_bw"]/100
  dd["txlen"] = root["chirp_len"]
  #dd["chirpAmp"] = root["chirp_amp"]
  dd["txPRF"] = root["prf"]
  dd["fs"] = 1.0/root["dt"]
  dd["stack"] = root["stacking"]
  dd["spt"] = root["record_len"]
  dd["trlen"] = root["dt"] * dd["spt"]
  
  # Some files have "pulse" and not "bark"
  try:
    bark = root["bark"]
  except KeyError:
    bark = root["pulse"]
    
  try:
    bark_len = root["bark_len"]
  except KeyError:
    bark_len = root["pulse_len"]

  try:
    bark_delay = root["bark_delay"]
  except KeyError:
    bark_delay = root["pulse_delay"]
    
  spb = int(np.ceil((bark_len+bark_delay)*dd["fs"]))
  
  # Extract ch0
  dd["rx0"] = tdmsSlice(ch0, dd["spt"], bark, spb)
  
  # Correct double length metadata error, or trim data
  if(len(lat) > 2*dd["rx0"].shape[1]):
    lat = lat[0:len(lat)-1:2]
    lon = lon[0:len(lon)-1:2]
    elev = elev[0:len(elev)-1:2]
    time = time[0:len(time)-1:2]
  else:
    lat = lat[0:len(lat)-1]
    lon = lon[0:len(lon)-1]
    elev = elev[0:len(elev)-1]
    time = time[0:len(time)-1]
    
  if(len(time) < 50):
    sys.stdout.write("Less than 50 traces, skipping: ")
    return -1
    
  # Fill in every other time value
  for i in range(len(time)-1):
    if(time[i] == 0):
      time[i] = (time[i-1] + time[i+1])/2
      
  # Fill in last time value
  diff = time[-2] - time[-3]
  time[-1] = time[-2] + diff
  
  # Time -> seconds since unix epoch
  time = time.astype(np.float64)
  epoch = datetime.utcfromtimestamp(0)
  initT = timedelta(0,time[0])
  for i in range(len(time)):
    delta = timedelta(0, time[i]) - initT
    time[i] = ((startTime + delta)-epoch).total_seconds()
        
  # Crop metadata if rx0 shorter
  nt = dd["rx0"].shape[1]
  lat = lat[:nt]
  lon = lon[:nt]
  elev = elev[:nt]
  time = time[:nt]
  
  # Get rid of traces with non-unique time
  time, ai = np.unique(time, return_index=True)
  lat = lat[ai]
  lon = lon[ai]
  elev = elev[ai]
  dd["rx0"] = dd["rx0"][:,ai]
    
  dd["ntrace"] = dd["rx0"].shape[1]
  dd["rx0"] = dd["rx0"][:,0:dd["ntrace"]].astype(np.float32)
  
  dd["lat"] = np.zeros(dd["ntrace"]).astype("float")
  dd["lon"] = np.zeros(dd["ntrace"]).astype("float")
  dd["alt"] = np.zeros(dd["ntrace"]).astype("float")
  dd["tfull"] = np.zeros(dd["ntrace"]).astype("int64")
  dd["tfrac"] = np.zeros(dd["ntrace"]).astype("double")

  for i in range(dd["ntrace"]):
    #print(time[i], lat[i], lon[i], elev[i])
    dd["tfull"][i] = int(time[i]) - 37 # GPS to UTC
    dd["tfrac"][i] = time[i] - int(time[i])
    dd["lat"][i] = lat[i]
    dd["lon"][i] = lon[i]
    dd["alt"][i] = elev[i]

  # Rotate out HW delay
  date = datetime.utcfromtimestamp(dd["tfull"][i] + dd["tfrac"][i])

  if(date.year != 2018 and date.month not in (5,8)):
    print("Unknown tdms data source")
    sys.exit(1)

  # Handle offset changes over campaign
  # May is constant, but a split in Aug
  if(date.month == 5):
    dd["rx0"] = np.roll(dd["rx0"], -14, axis=0)
  elif(date.month == 8 and date.day in (17,18,19,20)):
    dd["rx0"] = np.roll(dd["rx0"], 158, axis=0)
  elif(date.month == 8):
    dd["rx0"] = np.roll(dd["rx0"], 14, axis=0)
  else:
    print("NO OFFSET CORRECTION FOUND\n\t" + fname)
    exit()

  return dd