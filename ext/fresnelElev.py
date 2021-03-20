import numpy as np
import h5py, glob, sys, json, subprocess, os
from osgeo import gdal, osr, ogr
import pdal
import xml.etree.ElementTree as et
import pandas as pd
import laspy.file as lasf
import numexpr as ne
import argparse
from multiprocessing import Pool
import logging as log

# Open an hdf5 file
# Open las db
# Open correct las files
# Merge them if necessary with pdal
# Iterate thru nav and use pdal to extract fresnel zone of points
# Take avg elev of this, use as surface elev


def lasOpen(lasDir, h5file):
    # Open las db
    lasdb = open(lasDir + "/lasDB.json", "r")
    db = json.load(lasdb)
    lasdb.close()

    # Get list of las files
    lasfiles = db[h5file.split("/")[-1]].keys()
    lasfiles = list(lasfiles)
    if len(lasfiles) == 0:
        log.warning("%s has no associated LAS files", os.path.basename(h5file))
        return ([], [], [], [])

    lshort = []
    for file in lasfiles:
      lshort.append(os.path.basename(file))
    log.info("%s matched to %s", os.path.basename(h5file), lshort)
    # Open and merge las files into one array

    f = lasf.File(lasDir + "/" + lasfiles[0], mode="r")
    xl = f.x
    yl = f.y
    zl = f.z
    f.close()

    if len(lasfiles) > 1:
        for i in range(1, len(lasfiles)):
            f = lasf.File(lasDir + "/" + lasfiles[i], mode="r")
            xl = np.append(xl, f.x)
            yl = np.append(yl, f.y)
            zl = np.append(zl, f.z)
            f.close()

        # Check that same coordinate system assumption is valid
    crs = [None] * len(lasfiles)
    for i in range(len(lasfiles)):
        # info = subprocess.run(['lasinfo', '--xml', sys.argv[1] + "/" + lasfiles[i]], stdout=subprocess.PIPE)
        # going to try with pdal instead
        info = subprocess.run(
            ["pdal", "info",lasDir + "/" + lasfiles[i], "--metadata"],
            stdout=subprocess.PIPE,
        )

        # decode stdout from bytestring and convert to a dictionary
        json_result = json.loads(info.stdout.decode())

        # # Parse xml
        # root = et.fromstring(info.stdout)

        # Coordinate reference system
        # crs[i] = root.find("header").find("srs").find("wkt").text
        crs[i] = json_result["metadata"]["srs"]["wkt"]

    # Set only contains unique
    if len(set(crs)) > 1:
        log.warning("%s not all coordinate systems the same %s", os.path.basename(h5file), lshort)
        return 1

    return (xl, yl, zl, crs[0])


def surfXtract(traj, xl, yl, zl, wavel, operation="median"):
    srf = -9999*np.ones(len(traj.GetPoints()))
    c = np.zeros(len(traj.GetPoints())).astype(np.uint32)
    for i, point in enumerate(traj.GetPoints()):
        xt = point[0]
        yt = point[1]
        zt = point[2]
        fz = ne.evaluate("(xl-xt)**2 + (yl-yt)**2 <= (zt-zl)*wavel/2 + wavel/16")
        # fz = (xl-xt)**2 + (yl-yt)**2 <= (zt-zl)*wavel/2 + wavel/16
        surfZ = zl[fz]
        c[i] = len(surfZ)
        if len(surfZ) != 0:
            srf[i] = np.median(surfZ)
        # print(i, len(surfZ), srf[i], np.mean(surfZ), np.median(surfZ))
    return c, srf


def xtractWrap(lasDir, data, odir):
    log.info("Starting extraction for " + os.path.basename(data))
    xl, yl, zl, crs = lasOpen(lasDir, data)
    if(len(xl) == 0):
        return 0

    ofile = odir + '/' + data.split('/')[-1].replace(".h5", "")
    log.info("Output will be written to " + ofile)
    
    f = h5py.File(data, "r+")

    if "nav0" in f["ext"].keys():
        trajR = f["ext"]["nav0"]
    else:
        #trajR = f["raw"]["loc0"]
        log.warning("No /ext/nav0 dataset found for " + os.path.basename(data))
        f.close() # Exit because this was not during a flight
        return 0

    sig = f["raw"]["tx0"].attrs["signal"]

    wavel = 3e8 / f["raw"]["tx0"].attrs["centerFrequency"][0]

    isrs = osr.SpatialReference()
    isrs.ImportFromEPSG(4326)  # WGS84 locations
    osrs = osr.SpatialReference()
    osrs.ImportFromWkt(crs)

    # Build trajectory then transform to point coordinates
    traj = ogr.Geometry(ogr.wkbLineString)
    for point in trajR:
        traj.AddPoint(
            point[0].astype(np.double),
            point[1].astype(np.double),
            point[2].astype(np.double),
        )

    traj.AssignSpatialReference(isrs)
    traj.TransformTo(osrs)

    count, srf = surfXtract(traj, xl, yl, zl, wavel)

    log.info("Surface extraction complete for " + os.path.basename(data))
    # Save to csv instead of straight to hdf5 file, to skip generation later
    np.savetxt(ofile+"_srf.csv", srf, fmt="%.3f", delimiter=',')
    np.savetxt(ofile+"_count.csv", count, fmt="%d", delimiter=',')

#    srf0 = f["ext"].require_dataset("srf0", shape=srf.shape, data=srf, dtype=np.float32)
#    srf0.attrs.create("unit", np.string_("meter"))
#    srf0.attrs.create("verticalDatum", np.string_("WGS84 Ellipsoid"))

#    srf0count = f["ext"].require_dataset("srf0count", shape=count.shape, data=count, dtype=np.uint32)

    # Add in twtt_surf dataset
#    c = 299792458  # Speed of light at STP

#    elev_air = f["ext"]["nav0"]["hgt"][:]

#    twtt_surf = 2 * (elev_air - srf) / c

#    twtt_surf_pick = f["drv"]["pick"].require_dataset(
#        "twtt_surf", data=twtt_surf, shape=twtt_surf.shape, dtype=np.float32
#    )
#    twtt_surf_pick.attrs.create("unit", np.string_("second"))

    f.close()

    return 0

def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program for extraction of a radar surface from a lidar dataset"
    )
    parser.add_argument("odir", help="Output directory for derived surface files")
    parser.add_argument("lidar", help="Directory of lidar files and lidar DB")
    parser.add_argument("data", help="Data file(s)", nargs="+")
    parser.add_argument(
        "-n",
        "--num-proc",
        type=int,
        help="Number of simultaneous processes, default 1",
        default=1,
    )
    args = parser.parse_args()
    
    # Set up logging
    log.basicConfig(
        filename=os.path.dirname(args.data[0]) + "/fresnelElev.log",
        format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
        level=log.INFO,
    )

    # Print warning and error to stderr
    sh = log.StreamHandler()
    sh.setLevel(log.WARNING)
    sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
    log.getLogger("").addHandler(sh)
    
    log.info("Starting lidar surface extraction")
    log.info("num_proc %s", args.num_proc)
    log.info("odir %s", args.odir)
    log.info("lidar %s", args.lidar)
    log.info("data %s", args.data)

    lidar = [args.lidar] * len(args.data)
    odir = [args.odir] * len(args.data)

    p = Pool(args.num_proc)
    p.starmap(xtractWrap, zip(lidar, args.data, odir))
    p.close()
    p.join()


main()
