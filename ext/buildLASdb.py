# Input 1 is a las directory, input 2 is a directory with radar hdf5 files
# Build json database with overlap info for LAS bounding boxes
# Use julian day in lidar file name to match with appropriate radar file timestamp

import h5py, glob, sys, json, datetime
from pytz import timezone
import pandas as pd

h5Files = glob.glob(sys.argv[2] + "/*.h5")
outd = {}
outf = open(sys.argv[1] + "/lasDB.json", 'w')
colNames = ["file","minLon","minLat","maxLon","maxLat"]
lasIndex = pd.read_csv(sys.argv[1] + "/lasIndex.csv", header=None, names=colNames)

for file in h5Files:
    f = h5py.File(file,'r')
    fname = file.split("/")[-1]
    print(f["raw"]["time0"][0][0])
    startT = datetime.datetime.utcfromtimestamp(f["raw"]["time0"][0][0] + f["raw"]["time0"][0][1])
    utc2ak = datetime.timedelta(hours=8)
    startT = startT - utc2ak
    jday = startT.timetuple().tm_yday
    outd.update({fname : {}})

    if("nav0" in f["ext"].keys()):
        traj = f["ext"]["nav0"][:]
    else: # Use loc0 from raw
      traj = f["raw"]["loc0"][:]

    f.close()

    for i, lasf in lasIndex.iterrows():
        # Check for julian day match with filename
        if(lasf["file"].split('_')[2] != str(jday)):
                continue

        elif lasf["file"].endswith("laz"):
            if(lasf["file"][5:8] != str(jday)):
                continue

        # See if radar file track falls within lidar file extent
        # Initial rough check - only every 100th traces
        ct = 0
        for trajP in traj[::100]:
            lat = trajP[0]
            lon = trajP[1]

            if(lat > lasf["minLat"] and lat < lasf["maxLat"] and lon > lasf["minLon"] and lon < lasf["maxLon"]):
                ct += 1

        if(ct == 0):
            continue

        # If anything passes rough check - do fine check and save to dict
        ct = 0
        for trajP in traj:
            lat = trajP[0]
            lon = trajP[1]
            if(lat > lasf["minLat"] and lat < lasf["maxLat"] and lon > lasf["minLon"] and lon < lasf["maxLon"]):
                ct += 1
        fdict = outd[fname]
        fdict.update({lasf["file"] : ct})

json.dump(outd, outf)
outf.close()
