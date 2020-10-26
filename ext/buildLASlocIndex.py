# Input is a directory path
# Builds an index of all of the LAS files in that directory
# in the format:
# filename,minlat,minlon,maxlat,maxlon
# Lat and lon are wgs84

### colugo environment: pdal ###

from osgeo import gdal, osr, ogr
import glob, sys, subprocess, pdal, json
#import xml.etree.ElementTree as et

lasFiles = glob.glob(sys.argv[1] + "/*.la?")
outf = open(sys.argv[1] + "/lasIndex.csv", 'w')

for file in lasFiles:
    '''
    # Get xml fmt info
    info = subprocess.run(['/zippy/MARS/syst/ext/linux/LAStools/bin/lasinfo', '--xml', file], stdout=subprocess.PIPE)

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

    '''
    # use pdal to get lidar file extent and crs
    info = subprocess.run(['pdal', 'info', file],
                        stderr = subprocess.PIPE,  # stderr and stdout get
                        stdout = subprocess.PIPE)  # captured as bytestrings

    # decode stdout from bytestring and convert to a dictionary
    json_result = json.loads(info.stdout.decode())

    # bounding box info dict
    bbox = json_result['stats']['bbox']

    # data crs
    crs_str = list(bbox.keys())[0]

    # get extents
    minx = bbox[crs_str]['bbox']['minx']
    miny = bbox[crs_str]['bbox']['miny']
    maxx = bbox[crs_str]['bbox']['maxx']
    maxy = bbox[crs_str]['bbox']['maxy']

    # Coordinate conversion
    isrs = osr.SpatialReference()
    isrs.ImportFromEPSG(int(crs_str[-4:]))
    osrs = osr.SpatialReference()
    osrs.ImportFromEPSG(4326)
    # cretea bounding points
    minp = ogr.Geometry(ogr.wkbPoint)
    maxp = ogr.Geometry(ogr.wkbPoint)

    # add min and max extent points
    minp.AddPoint(minx,miny)
    maxp.AddPoint(maxx,maxy)

    # ensure points are in EPSG 4326
    minp.AssignSpatialReference(isrs)
    maxp.AssignSpatialReference(isrs)

    minp.TransformTo(osrs)
    maxp.TransformTo(osrs)

    print(file, minx,miny, maxx, maxy)

    ## format of output ###
    ["file","minLon","minLat","maxLon","maxLat"]
    
    # Write output
    outf.write("%s,%.6f,%.6f,%.6f,%.6f\n" % (file.split("/")[-1],minp.GetX(),minp.GetY(),maxp.GetX(),maxp.GetY()))

# close file
outf.close()