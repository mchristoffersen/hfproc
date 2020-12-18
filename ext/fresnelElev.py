import numpy as np
import h5py, glob, sys, json, subprocess
from osgeo import gdal, osr, ogr
import pdal
import xml.etree.ElementTree as et
import pandas as pd
import laspy.file as lasf
import numexpr as ne


# Input 1 is las directory
# Input 2 is path to hdf5 file

# Open an hdf5 file
# Open las db
# Open correct las files
# Merge them if necessary with pdal
# Iterate thru nav and use pdal to extract fresnel zone of points
# Take avg elev of this, use as surface elev

def lasOpen(lasDir, h5file):
  # Open las db
  lasdb = open(lasDir + "/lasDB.json", 'r')
  db = json.load(lasdb)
  lasdb.close()

  # Get list of las files
  lasfiles = db[h5file.split('/')[-1]].keys()
  lasfiles = list(lasfiles)
  print(lasfiles)
  if(len(lasfiles) == 0):
    print(h5file + " has no associated LAS files. Exiting.")
    exit()

  # Open and merge las files into one array

  f = lasf.File(lasDir + "/" + lasfiles[0], mode='r')
  xl = f.x
  yl = f.y
  zl = f.z
  f.close()

  if(len(lasfiles) > 1):
    for i in range(1,len(lasfiles)):
      f = lasf.File(lasDir + "/" + lasfiles[i], mode='r')
      xl = np.append(xl, f.x)
      yl = np.append(yl, f.y)
      zl = np.append(zl, f.z)
      f.close()

    # Check that same coordinate system assumption is valid
  crs = [None]*len(lasfiles)
  for i in range(len(lasfiles)):
      # info = subprocess.run(['lasinfo', '--xml', sys.argv[1] + "/" + lasfiles[i]], stdout=subprocess.PIPE)
      # going to try with pdal instead
      info = subprocess.run(['pdal', 'info', sys.argv[1] + "/" + lasfiles[i], "--metadata"], stdout=subprocess.PIPE)

      # decode stdout from bytestring and convert to a dictionary
      json_result = json.loads(info.stdout.decode())

      # # Parse xml
      # root = et.fromstring(info.stdout)

      # Coordinate reference system
      # crs[i] = root.find("header").find("srs").find("wkt").text
      crs[i] = json_result["metadata"]["srs"]["wkt"]

  # Set only contains unique
  if(len(set(crs)) > 1):
      print("Not all coordinate systems the same")
      exit()
      
  return (xl, yl, zl, crs[0])
        
def surfXtract(traj, xl, yl, zl, wavel, operation='median'):
  srf = np.zeros(len(traj.GetPoints()))
  for i, point in enumerate(traj.GetPoints()):
    xt = point[0]
    yt = point[1]
    zt = point[2]
    fz = ne.evaluate("(xl-xt)**2 + (yl-yt)**2 <= (zt-zl)*wavel/2 + wavel/16")
    #fz = (xl-xt)**2 + (yl-yt)**2 <= (zt-zl)*wavel/2 + wavel/16
    surfZ = zl[fz]
    if(len(surfZ) == 0):
      srf[i] = np.nan
    else:
      if operation == "median":
        srf[i] = np.median(surfZ)
      elif operation == "mean":
        srf[i] = np.mean(surfZ)
    #print(i, len(surfZ), srf[i], np.mean(surfZ), np.median(surfZ))
  return srf

def main():
  print(sys.argv[1],sys.argv[2], sys.argv[3])

  xl,yl,zl,crs = lasOpen(sys.argv[1], sys.argv[2])
  #operation = sys.argv[3]     # take median or mean of lidar fresnel zone elevations

  f = h5py.File(sys.argv[2], "r+")
  #f = h5py.File(sys.argv[2], "r")

  if("nav0" in f["ext"].keys()):
      trajR = f["ext"]["nav0"]
  else: # Use loc0 from raw
      trajR = f["raw"]["loc0"]

  sig = f["raw"]["tx0"].attrs["signal"]

  if(sig == b"chirp"):
    wavel = 3e8/f["raw"]["tx0"].attrs["centerFrequency"]
  else:
    wavel = 120

  isrs = osr.SpatialReference()
  isrs.ImportFromEPSG(4326) #WGS84 locations
  osrs = osr.SpatialReference()
  osrs.ImportFromWkt(crs)

  # Build trajectory then transform to point coordinates
  traj = ogr.Geometry(ogr.wkbLineString)
  for point in trajR:
      traj.AddPoint(point[0].astype(np.double),point[1].astype(np.double),point[2].astype(np.double))

  traj.AssignSpatialReference(isrs)
  traj.TransformTo(osrs)

  srf = surfXtract(traj, xl, yl, zl, wavel)
  
  srf0 = f["ext"].require_dataset("srf0", shape=srf.shape, data=srf, dtype=np.float32)
  srf0.attrs.create("unit", np.string_("meter"))
  srf0.attrs.create("verticalDatum", np.string_("WGS84 Ellipsoid"))
  f.close()
  print(sys.argv[2])

  
main()
