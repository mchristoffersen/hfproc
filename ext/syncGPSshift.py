import h5py
import numpy as np
import pandas as pd
import sys, os
import datetime
import argparse
import logging as log

# TODO: change structure of this program
# Read in nav files to individual arrays instead of one big one
#  - also try to speed up nav file read in
# For each radar file check which nav file it falls into and only
# use that data for interp, not the whole array
# Report if a radar file is outside of nav files, this is likely a test on the ground
# Also multiprocess the nav file read in and the interpolation

class Trajectory:
  def __init__(self, fullS, fracS, lat, lon, elev, file):
    self.fullS = fullS
    self.fracS = fracS
    self.lat = lat
    self.lon = lon
    self.hgt = elev
    t = (self.fullS+self.fracS)
    self.startT = t.min()
    self.stopT = t.max()
    self.file = file
    
def navIngest(nav):
    # Ingest all .pos files listed in the nav variable
    # Change UTD TOD to format of Ettus time stamp (time since Jan 1, 1970?)
    # Also GPS to UTC correction ?
    # Produce 5 lists [fullS,...] [fracS,...] [lat,...] [lon,...] [elev,...]
    # Also a dict with metadata for each array entry
    # Return for use in navcalc
    
    tracks = []

    for file in nav:
        log.info("Loading file " + os.path.basename(file))
        # read in .pos data files
        if file.split(".")[-1] == "pos":
            cols = ["tod", "lat", "lon", "h"]  # , "roll", "pitch", "hdg"]
            nav = pd.read_csv(file, header=0, names=cols, delimiter=" ", usecols=cols)

            # Extract YYYY/MM/DD from file name
            fn = file.split("/")[-1]
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
                frac[i] = nav["tod"][i] % 1
                todfull = int(nav["tod"][i])
                if (
                    todfull < prevtod
                ):  # If day rolls over then add a days worth of seconds
                    rollover = 86400
                prevtod = todfull
                full[i] = s + todfull + rollover

        # read in .csv data files
        if file.split(".")[-1] == "csv":
            cols = ["week", "jd", "sow", "lat", "lon", "h"]
            nav = pd.read_csv(file, header=None, names=cols, delimiter=",")
            fn = file.split("/")[-1]

            epoch = datetime.datetime.utcfromtimestamp(0)
            gps = datetime.datetime(1980, 1, 6, hour=0, minute=0, second=0)

            # Open and concatenate all files in order
            full = np.empty((len(nav)), dtype=np.uint64)
            frac = np.empty((len(nav)), dtype=np.double)

            for i in range(len(nav)):
                dt = datetime.timedelta(
                    days=int(nav["week"][i] * 7), seconds=int(nav["sow"][i] - 16)
                )  # Only 2013 data with 16 leap secs
                full[i] = int(
                    ((gps + dt) - epoch).total_seconds()
                )  # Only whole seconds
                frac[i] = 0

        traj = Trajectory(full, frac, nav["lat"].to_numpy(dtype=np.float64), nav["lon"].to_numpy(dtype=np.float64), nav["h"].to_numpy(dtype=np.float64), file)

        tracks.append(traj)

    return tracks

def navCalc(time, track):
    # Sample nav arrays at Ettus time points, linearly interpolate for inexact match

    minFull = track.fullS.min()
    lidarTime = np.subtract(track.fullS, minFull)
    lidarTime = np.add(lidarTime, track.fracS)
    radarTime = np.subtract(time[0], minFull)
    radarTime = np.add(radarTime, time[1])

    # print(len(lidarTime), len(fix[3]))
    lati = np.interp(radarTime, lidarTime, track.lat)
    loni = np.interp(radarTime, lidarTime, track.lon)
    hgti = np.interp(radarTime, lidarTime, track.hgt)

    nav_t = np.dtype([("lat", np.float32), ("lon", np.float32), ("hgt", np.float32)])

    nav = np.empty((len(lati)), dtype=nav_t)

    for i in range(len(nav)):
        nav[i] = (lati[i], loni[i], hgti[i])

    return nav


def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program for extraction of radar navidation from a denser GPS trajectory dataset"
    )
    parser.add_argument("nav", help="GPS trajectory file(s)", nargs="+")
    parser.add_argument("data", help="Data file(s)", nargs="+")
    args = parser.parse_args()

    # Set up logging
    log.basicConfig(
        filename=os.path.dirname(args.data[0]) + "/syncGPS.log",
        format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
        level=log.INFO,
    )

    # Print warning and error to stderr
    sh = log.StreamHandler()
    sh.setLevel(log.WARNING)
    sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
    log.getLogger("").addHandler(sh)
    
    # Sort nav and data
    nav = []
    data = []
    for f in args.nav + args.data:
        if f.split('.')[-1] in ["pos", "csv"]:
            nav.append(f)
        elif f.split('.')[-1] == "h5":
            data.append(f)
        else:
            print("Unknown file type:", f)
            exit()
            
    log.info("Starting GPS sync")
    log.info("nav %s", nav)
    log.info("data %s", data)

    tracks = navIngest(nav)
    log.info("Navigation data parsed and loaded")
    for file in data:
        f = h5py.File(file, "a")
        time = f["raw"]["time0"][:]
        tFull = np.empty((len(time)), dtype=np.uint64)
        tFrac = np.empty((len(time)), dtype=np.double)
        dt = -696
        log.warning("Adding " + str(dt) + "s to data time for nav xtract")
        for i in range(len(time)):
            tFull[i] = time[i][0]+dt
            tFrac[i] = time[i][1]

        # check if radar file start/stop times fall during nav file times
        match = 0
        for track in tracks:
            print(track.file)
            fstart = tFull[0]+tFrac[0]
            fstop = tFull[-1]+tFrac[-1]
            print(fstart > track.startT, fstart < track.stopT)
            print(fstart > track.startT, fstop < track.stopT)
            if ((tFull[0]+tFrac[0]) >= track.startT) and ((tFull[-1]+tFrac[-1]) <= track.stopT):
                match = 1
                log.info("Matched data " + os.path.basename(file) + " to track " + os.path.basename(track.file))
                # nav dataset
                nav_t = np.dtype(
                    [("lat", np.float32), ("lon", np.float32), ("hgt", np.float32)]
                )

                nav = navCalc([tFull, tFrac], track)
                nav0 = f["ext"].require_dataset(
                    "nav0", shape=nav.shape, data=nav, dtype=nav_t
                )
                nav0[:] = nav[:]
                nav0.attrs.create("CRS", np.string_("WGS84"))
 
                # exit
                break
    
        if(not match):
          log.warning("Unable to match track for " + os.path.basename(file))
            
        # close file
        f.close()

main()
