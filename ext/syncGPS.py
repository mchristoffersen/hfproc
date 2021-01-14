import h5py
import numpy as np
import pandas as pd
import sys, os
import glob
import datetime
import matplotlib.pyplot as plt
import datetime


def navIngest(dir):
  # Ingest all .pos files in a directory
  # Change UTD TOD to format of Ettus time stamp (time since Jan 1, 1970?)
  # Also GPS to UTC correction ?
  # Produce 4 arrays [fullS,...] [fracS,...] [lat,...] [lon,...] [elev,...]
  # Return for use in navcalc
  time_t = np.dtype([('fullS', np.uint64),
                     ('fracS', np.float64)])

  fullS = np.array([]).astype(np.uint64)
  fracS = np.array([]).astype(np.double)
  lats = np.array([]).astype(np.float)
  lons = np.array([]).astype(np.float)
  alts = np.array([]).astype(np.float)

  files = glob.glob(dir+"/*.pos") + glob.glob(dir+"/*.csv")
  files.sort()

  print(files)
  for file in files:
    # read in .pos data files
    if(file.split('.')[-1] == "pos"):
      cols = ["tod", "lat", "lon", "h"] #, "roll", "pitch", "hdg"]
      nav = pd.read_csv(file, header=0, names=cols, delimiter=" ", usecols=cols)

      # Extract YYYY/MM/DD from file name
      fn = file.split('/')[-1]
      print(fn)
      year = 2000 + int(fn[0:2])
      month = int(fn[2:4])
      day = int(fn[4:6])

      # Find seconds since epoch for 00:00:00
      epoch = datetime.datetime.utcfromtimestamp(0)
      t = datetime.datetime(year, month, day)
      s = int((t - epoch).total_seconds())

      # Open and concatenate all files in order
      full = np.empty((len(nav)), dtype=np.uint64)
      frac = np.empty((len(nav)), dtype=np.double)
      prevtod = -1
      rollover = 0

      for i in range(len(full)):
        frac[i] = nav["tod"][i]%1
        todfull = int(nav["tod"][i])
        if(todfull < prevtod): # If day rolls over then add a days worth of seconds
          rollover = 86400
        prevtod = todfull
        full[i] = s + todfull + rollover


    # read in .csv data files
    if(file.split('.')[-1] == "csv"):
      cols = ["week", "jd", "sow", "lat", "lon", "h"]
      nav = pd.read_csv(file, header=None, names=cols, delimiter=',')
      fn = file.split('/')[-1]
      print(fn)

      epoch = datetime.datetime.utcfromtimestamp(0)
      gps = datetime.datetime(1980, 1, 6, hour=0, minute=0, second=0)
      
      # Open and concatenate all files in order
      full = np.empty((len(nav)), dtype=np.uint64)
      frac = np.empty((len(nav)), dtype=np.double)

      for i in range(len(nav)):
        dt = datetime.timedelta(days=int(nav["week"][i]*7),seconds=int(nav["sow"][i] - 16)) # Only 2013 data with 16 leap secs
        full[i] = int(((gps + dt) - epoch).total_seconds()) # Only whole seconds
        frac[i] = 0

    lats = np.append(lats, nav["lat"].to_numpy())
    lons = np.append(lons, nav["lon"].to_numpy())
    alts = np.append(alts, nav["h"].to_numpy())
    fullS = np.append(fullS, full)
    fracS = np.append(fracS, frac)

  return (fullS, fracS, lats, lons, alts)

def navCalc(time, fix):
    # Sample nav arrays at Ettus time points, linearly interpolate for inexact match

    minFull = min(fix[0])
    lidarTime = np.subtract(fix[0], minFull)
    lidarTime = np.add(lidarTime, fix[1])
    radarTime = np.subtract(time[0], minFull)
    radarTime = np.add(radarTime, time[1])

    # print(len(lidarTime), len(fix[3]))
    lati = np.interp(radarTime, lidarTime, fix[2])
    loni = np.interp(radarTime, lidarTime, fix[3])
    alti = np.interp(radarTime, lidarTime, fix[4])

    nav_t = np.dtype([("lat", np.float32), ("lon", np.float32), ("altM", np.float32)])

    nav = np.empty((len(lati)), dtype=nav_t)

    for i in range(len(nav)):
        nav[i] = (lati[i], loni[i], alti[i])

    return nav


def readrow(row, cols):
    # read text file from string to handle rows with missing data
    a = np.fromstring(row, sep=" ")
    a.resize((cols,))
    return a


def main():
    # Maybe just loop over all files in here so ingest is not redone for each
    # Or seperate ingester and make intermediate product to use

    navdir = sys.argv[1]
    fdir = sys.argv[2]
    print("Nav Directory: " + navdir)
    print("Data Directory: " + fdir)
    print()
    fix = navIngest(navdir)
    for path in os.listdir(fdir):
        if path.endswith(".h5"):
            print(path)
            f = h5py.File(fdir + "/" + path, "a")
            time = f["raw"]["time0"][:]
            tFull = np.empty((len(time)), dtype=np.uint64)
            tFrac = np.empty((len(time)), dtype=np.double)
            for i in range(len(time)):
                tFull[i] = time[i][0]
                tFrac[i] = time[i][1]

            # nav dataset
            nav_t = np.dtype(
                [("lat", np.float32), ("lon", np.float32), ("altM", np.float32)]
            )

            nav = navCalc([tFull, tFrac], fix)
            nav0 = f["ext"].require_dataset(
                "nav0", shape=nav.shape, data=nav, dtype=nav_t
            )
            nav0.attrs.create("CRS", np.string_("WGS84"))

            f.close()


main()
