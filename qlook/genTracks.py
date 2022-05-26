# Generate a geopackage containing the observation tracks for a given year
import sys, os, h5py
from datetime import datetime
import geopandas as gpd
from shapely.geometry import LineString
import argparse

def main():
    # Maybe just loop over all files in here so ingest is not redone for each
    # Or seperate ingester and make intermediate product to use

    fdir = sys.argv[1]
    outf = sys.argv[2]
    gdf = gpd.GeoDataFrame(
        geometry=[],
        columns=[
            "radar",
            "stop_time",
            "start_time",
            "fname",
            "day",
            "month",
            "year",
            "ntrace",
            "centerFreq",
        ],
    )
    gdf.crs = "EPSG:4326"
    for path in os.listdir(fdir):
        if path.endswith(".h5"):
            print(path)
            row = {}

            f = h5py.File(fdir + "/" + path, "r")

            if("nav0" not in f["ext"].keys()):
                print("NO NAV IN " + path + " USING LOC")
                nav0 = f["raw"]["loc0"][:]
                print("SUBSAMPLING BY 10")
                nav0 = nav0[::10]
                #f.close()
                #continue
            else:
                nav0 = f["ext"]["nav0"][:]

            if len(nav0) < 2:
                f.close()
                continue

            #loc0 = [(lon, lat, elev) for (lat, lon, elev) in loc0]
            nav0 = [(lon, lat, elev) for (lat, lon, elev) in nav0]

            # loc0 = f["ext"]["nav0"][:]
            # loc0 = [(lon, lat, elev) for (lat, lon, elev) in loc0]

            row["geometry"] = LineString(nav0)
            #row["radar"] = "LoWRES"
            tstart = f["raw"]["time0"][0]
            tstart = tstart[0] + tstart[1]
            tstart = datetime.utcfromtimestamp(tstart)

            tstop = f["raw"]["time0"][-1]
            tstop = tstop[0] + tstop[1]
            tstop = datetime.utcfromtimestamp(tstop)

            row["start_time"] = tstart.strftime("%H:%M:%S")
            row["stop_time"] = tstop.strftime("%H:%M:%S")

            row["year"] = tstart.year
            row["month"] = tstart.month
            row["day"] = tstart.day

            #row["centerFreq"] = f["raw"]["tx0"].attrs["CenterFrequency-Hz"]
            row["ntrace"] = f["raw"]["rx0"].attrs["numTrace"]

            row["fname"] = path
            f.close()
            gdf = gdf.append(row, ignore_index=True)

    gdf.to_file(outf, layer=str(tstart.year), driver="GPKG")

"""
def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program to create a shapefile of the trajectories in /ext/nav0 or /raw/loc0"
    )
    parser.add_argument("dest", help="Output file")
    parser.add_argument("data", help="Data file(s)", nargs="+")
    args = parser.parse_args()
"""

main()
