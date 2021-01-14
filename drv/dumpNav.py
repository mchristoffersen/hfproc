import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt


def main():
    hdfFile = sys.argv[1]
    outFile = sys.argv[2] + "/" + sys.argv[1].split("/")[-1].replace(".h5", ".csv")
    print(hdfFile)
    f = h5py.File(hdfFile, "r")
    if "nav0" in f["ext"].keys():
        traj = f["ext"]["nav0"][:]
    else:  # Use loc0 from raw
        traj = f["raw"]["loc0"][:]
    f.close()
    of = open(outFile, "w")
    for p in traj:
        of.write(str(p[0]) + "," + str(p[1]) + "," + str(p[2]) + "\n")
    of.close()


main()
