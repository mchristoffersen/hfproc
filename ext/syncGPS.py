import h5py
import numpy as np
import pandas as pd
import sys, os
import glob
import datetime
import matplotlib.pyplot as plt
import datetime
import argparse


def navIngest(nav):
    # Ingest all .pos files listed in the nav variable
    # Change UTD TOD to format of Ettus time stamp (time since Jan 1, 1970?)
    # Also GPS to UTC correction ?
    # Produce 4 arrays [fullS,...] [fracS,...] [lat,...] [lon,...] [elev,...]
    # Return for use in navcalc
    time_t = np.dtype([("fullS", np.uint64), ("fracS", np.float64)])

    fullS = np.array([]).astype(np.uint64)
    fracS = np.array([]).astype(np.double)
    lats = np.array([]).astype(np.float)
    lons = np.array([]).astype(np.float)
    alts = np.array([]).astype(np.float)

    # initialize dictionary to hold start/stop times for each nav file
    navtimes = {}

    for file in nav:
        # read in .pos data files
        if file.split(".")[-1] == "pos":
            cols = ["tod", "lat", "lon", "h"]  # , "roll", "pitch", "hdg"]
            nav = pd.read_csv(file, header=0, names=cols, delimiter=" ", usecols=cols)

            # Extract YYYY/MM/DD from file name
            fn = file.split("/")[-1]
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
            print(fn)

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

        lats = np.append(lats, nav["lat"].to_numpy())
        lons = np.append(lons, nav["lon"].to_numpy())
        alts = np.append(alts, nav["h"].to_numpy())
        fullS = np.append(fullS, full)
        fracS = np.append(fracS, frac)

        # add nav file start/stop times to dict
        navtimes[fn] = [full[0]+frac[0], full[-1]+frac[-1]]

    return (fullS, fracS, lats, lons, alts), navtimes

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


def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program for extraction of radar navidation from a denser GPS trajectory dataset"
    )
    parser.add_argument("nav", help="GPS trajectory file(s)", nargs="+")
    parser.add_argument("data", help="Raw data file(s)", nargs="+")
    args = parser.parse_args()

    # Sort nav and data
    nav = []
    data = []
    for f in args.nav:
        if f.split('.')[-1] == "pos":
            nav.append(f)
        elif f.split('.')[-1] == "h5":
            data.append(f)
        else:
            print("Unknown file type:", f)
            exit()
    
    fix, navtimes = navIngest(navdir)
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

            # check if radar file start/stop times fall during nav file times
            for times in navtimes.values():
                if ((tFull[0]+tFrac[0]) >= times[0]) and ((tFull[-1]+tFrac[-1]) <= times[-1]):

                    # nav dataset
                    nav_t = np.dtype(
                        [("lat", np.float32), ("lon", np.float32), ("altM", np.float32)]
                    )

                    nav = navCalc([tFull, tFrac], fix)
                    nav0 = f["ext"].require_dataset(
                        "nav0", shape=nav.shape, data=nav, dtype=nav_t
                    )
                    nav0.attrs.create("CRS", np.string_("WGS84"))
                    
                    # exit
                    break
            
            # close file
            f.close()

main()