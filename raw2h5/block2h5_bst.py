# imports
import sys, h5py, scipy.io
import numpy as np
from datetime import datetime
# import scipy as sp
from h5build import h5build
"""
block2h5 is a script to convert matplab block OIB-AK radar files to our modified hdf5 format
Brandon S. Tober
11AUG20


NOTE:
We may want to resave all .mat files as the same version for simpler ingest (7.3?). 
Also, time array may need to be converted from maltab string array to character array for 2018 data to be ingested in python
2015-2017 files seem to be of one structure, while 2018 is of another. No chirp data in 2015-2017 data, need to somehow handle this for h5 formatting.
"""

def parseBlock(fpath):
    dd = {}
    try:
        fd = h5py.File(fpath, "r")
        print(fpath.split("/")[-1],'h5py')

        # chirp sub-block
        chirp = fd["block"]["chirp"]
        dd["chirpCF"] = chirp["cf"][0][0]
        dd["chirpBW"] = chirp["bw"][0][0]
        dd["chirpLen"] = chirp["len"][0][0]       # need to deal with precision here, 5e-6 converted to 4.9999999999999996e-06
        dd["chirpAmp"] = chirp["amp"][0][0]

        dd["chirpPRF"] = fd["block"]["prf"][0][0]
        dd["fs"] = 1/fd["block"]["dt"][0][0]

        dd["stack"] = fd["block"]["stack"][0][0]
        dd["spt"] = fd["block"]["num_sample"][0][0]
        dd["traceLen"] = dd["spt"] / dd["fs"]

        ### do we want ch0, or amp????
        # extract ch0
        dd["rx0"] = np.array(fd["block"]["ch0"])
        dd["ntrace"] = dd["rx0"].shape[1]

        # navdat
        tfmt =  "%Y-%m-%dT%H:%M:%S.%f")

        time = fd["block"]["time"][0]
        #print(type(time), time.dtype, time.shape)
        print(time)
        sys.exit()
        dd["tfull"] = -1
        dd["tfrac"] = -1
        dd["lat"] = np.array(fd["block"]["lat"])
        dd["lon"] = np.array(fd["block"]["lon"])
        dd["alt"] = np.array(fd["block"]["elev_air"])
        dd["dop"] = np.repeat(-1, dd["ntrace"])
        dd["nsat"] = np.repeat(-1, dd["ntrace"])

    except:
        # use scipy.io.loadmat
        # has to be a better way than using all this 0-indexing
        fd = scipy.io.loadmat(fpath)
        print(fpath.split("/")[-1],"scio")

        # chirp sub-block
        chirp = fd["block"]["chirp"][0][0]
        dd["chirpCF"] = chirp["cf"][0][0][0][0]
        dd["chirpBW"] = chirp["bw"][0][0][0][0]
        dd["chirpLen"] = chirp["len"][0][0][0][0]       # need to deal with precision here, 5e-6 converted to 4.9999999999999996e-06
        dd["chirpAmp"] = chirp["amp"][0][0][0][0]

        dd["chirpPRF"] = fd["block"]["prf"][0][0][0][0]
        dd["fs"] = 1/fd["block"]["dt"][0][0][0][0]

        dd["stack"] = fd["block"]["stack"][0][0][0][0]
        dd["spt"] = fd["block"]["num_sample"][0][0][0][0]
        dd["traceLen"] = dd["spt"] / dd["fs"]

        ### do we want ch0, or amp????
        # extract ch0
        dd["rx0"] = fd["block"]["ch0"][0][0]
        dd["ntrace"] = dd["rx0"].shape[1]

        # navdat
        time = fd["block"]["time"][0][0][0]
        print(time)
        print(datetime.strptime(time[0], "%Y-%m-%dT%H:%M:%S.%f"))
        print(time)
        sys.exit()
        dd["tfull"] =-1
        dd["tfrac"] =-1
        dd["lat"] = fd["block"]["lat"][0][0][0]
        dd["lon"] = fd["block"]["lon"][0][0][0]
        dd["alt"] = fd["block"]["elev_air"][0][0][0]
        dd["dop"] = np.repeat(-1, dd["ntrace"])
        dd["nsat"] = np.repeat(-1, dd["ntrace"])

    print(dd)

def main():
  dd = parseBlock(sys.argv[1])
#   outf = sys.argv[2] + '/' + sys.argv[1].split('/')[-1].replace(".tdms",".h5")
#   print(outf)


#   # Open file
#   fd = h5py.File(outf, "w")

#   h5build(dd, fd)

  # Some basic info at file root
#   fd.attrs.create("Info", np.string_("Data acquired by the University of Texas Very Efficient Radar Very Efficient Team (VERVET) radar system"))
#   fd.close()

main()
