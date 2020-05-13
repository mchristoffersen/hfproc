# Input is a directory path
# Builds an index of all of the LAS files in that directory
# in the format:
# filename,minlat,minlon,maxlat,maxlon
# Lat and lon are wgs84

from osgeo import gdal, osr, ogr
import glob, sys, subprocess
import xml.etree.ElementTree as et

lasFiles = glob.glob(sys.argv[1] + "/*.las")
outf = open(sys.argv[1] + "/lasIndex.csv", 'w')

for file in lasFiles:
    # Get xml fmt info
    info = subprocess.run(['lasinfo', '--xml', file], stdout=subprocess.PIPE)
    
    # Parse xml
    root = et.fromstring(info.stdout)
    # Coordinate reference system
    srs = root.find("header").find("srs").find("wkt").text
    # min, max
    xmin = float(root.find("header").find("minimum").find("x").text)
    xmax = float(root.find("header").find("maximum").find("x").text)
    ymin = float(root.find("header").find("minimum").find("y").text)
    ymax = float(root.find("header").find("maximum").find("y").text)

    # Coordinate conversion
    isrs = osr.SpatialReference()
    isrs.ImportFromWkt(srs)
    osrs = osr.SpatialReference()
    osrs.ImportFromEPSG(4326)
    
    minp = ogr.Geometry(ogr.wkbPoint)
    maxp = ogr.Geometry(ogr.wkbPoint)
    
    minp.AddPoint(xmin,ymin)
    maxp.AddPoint(xmax,ymax)
    
    minp.AssignSpatialReference(isrs)
    maxp.AssignSpatialReference(isrs)
    
    minp.TransformTo(osrs)
    maxp.TransformTo(osrs)

    # Write output
    outf.write("%s,%.6f,%.6f,%.6f,%.6f\n" % (file.split("/")[-1],minp.GetY(),minp.GetX(),maxp.GetY(),maxp.GetX()))

outf.close()