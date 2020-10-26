import sys, h5py, scipy.io
import numpy as np
import scipy.signal as spsig
import scipy.stats as spstat
import matplotlib.pyplot as plt
from h5build import h5build
from datetime import datetime, timedelta
import pandas as pd

def parseRaw(fname):
  dd = {}

  fd = scipy.io.loadmat(fname)
  #fd = h5py.File(fname, 'r')

  ch0 = fd["block"]["ch0"][0][0]
  lat = fd["block"]["lat"][0][0]
  lon = fd["block"]["lon"][0][0]
  elev = fd["block"]["elev_air"][0][0]
  time = fd["block"]["time"][0][0][0]
  time = pd.to_datetime(time-719529, unit='D')
  dt = fd["block"]["dt"][0][0][0][0]

  if("chirp" in fd["block"].keys()):
    sig = "chirp"
  elif("wvrrm" in fd["block"].keys()):
    if(fd["block"]["wvfrm"] == "uaf-mono"):
      sig = "impulse"
    elif(fd["block"]["wvfrm"] == "utig-mono"):
      sig = "tone"
  else:
    print("Can't find TX signal info")
    sys.exit(1)

  #tr = np.sum(ch0, axis=1)
  # High pass in fast time
  #[b, a] = spsig.butter(4, 1.25e6, btype='highpass', fs=1.0/dt)
  #tr = scipy.signal.filtfilt(b, a, tr)

  #plt.plot(tr)
  #plt.show()
  
  #f, t, sxx = spsig.spectrogram(tr, fs=1.0/dt, window="blackmanharris",
  #                              nperseg=256, noverlap=220)
  #plt.imshow(sxx)
  #plt.hist(sxx.flatten())
  #plt.show()

  #plt.boxplot(sxx.flatten())
  #plt.show()

  #dscr = spstat.describe(sxx.flatten())
  #cut = dscr[2] + 25*dscr[3]
  #print(cut)

  #plt.pcolormesh(t/1e-6, f/1e6, sxx, shading='gouraud')
  #plt.ylabel('Frequency [MHz]')
  #plt.xlabel('Time [usec]')
  #plt.title(fname.split('/')[-1])
  #plt.show()
  #sys.exit()
"""
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
  
  dd["chirpCF"] = root["chirp_cf"]
  dd["chirpBW"] = root["chirp_bw"]/100
  dd["chirpLen"] = root["chirp_len"]
  dd["chirpAmp"] = root["chirp_amp"]
  dd["chirpPRF"] = root["prf"]
  dd["fs"] = 1.0/root["dt"]
  dd["stack"] = root["stacking"]
  dd["spt"] = root["record_len"]
  dd["traceLen"] = root["dt"] * dd["spt"]
  
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
  dd["dop"] = np.zeros(dd["ntrace"]).astype("float")
  dd["nsat"] = np.zeros(dd["ntrace"]).astype("int32")
  dd["tfull"] = np.zeros(dd["ntrace"]).astype("int64")
  dd["tfrac"] = np.zeros(dd["ntrace"]).astype("double")

  for i in range(dd["ntrace"]):
    #print(time[i], lat[i], lon[i], elev[i])
    dd["tfull"][i] = int(time[i]) - 37 # GPS to UTC
    dd["tfrac"][i] = time[i] - int(time[i])
    dd["lat"][i] = lat[i]
    dd["lon"][i] = lon[i]
    dd["alt"][i] = elev[i]
    dd["dop"][i] = -1
    dd["nsat"][i] = -1
  
  return dd
"""

def main():
  dd = parseRaw(sys.argv[1])
  #outf = sys.argv[2] + '/' + sys.argv[1].split('/')[-1].replace(".tdms",".h5")
  #print(outf)
  #if(dd == -1):
  #  exit()

  # Open file
  #fd = h5py.File(outf, "w")

  #h5build(dd, fd)

  # Some basic info at file root
  #fd.attrs.create("Info", np.string_("Data acquired by the University of Texas Very Efficient Radar Very Efficient Team (VERVET) radar system"))
  #fd.close()

main()
