# Input is a directory path
# Builds an index of all of the LAS files in that directory
# in the format:
# filename,startTime,stopTime
# Times are GPS seconds of day

import glob, sys, subprocess, json

lasFiles = glob.glob(sys.argv[1] + "/*.las")
outf = open(sys.argv[1] + "/lasIndex.csv", 'w')

for file in lasFiles:
    # Get xml fmt info
    info = subprocess.run(['pdal', 'info', file], stdout=subprocess.PIPE)
    
    # Parse xml
    info = json.loads(info.stdout)

    statlist = info["stats"]["statistic"]
    gpsTime = None
    for i in statlist:
        if(i["name"] == "GpsTime"):
            gpsTime = i
            break

    if(gpsTime == None):
        print("No GPS time found")
        exit()

    # Write output
    outf.write("%s,%.5f,%.5f\n" % (file.split("/")[-1],gpsTime["minimum"],gpsTime["maximum"]))

outf.close()