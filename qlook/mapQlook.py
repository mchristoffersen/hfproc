import h5py
import numpy as np
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import geotiler
from pyproj import Proj, transform

def saveMap(loc, name):
  minlat = np.min(loc["lat"])-.05
  minlon = np.min(loc["lon"])-.05
  maxlat = np.max(loc["lat"])+.05
  maxlon = np.max(loc["lon"])+.05

  gtm = geotiler.Map(extent=(minlon,minlat,maxlon,maxlat), zoom=11, provider="stamen-terrain")
  image = geotiler.render_map(gtm)
  w,h = image.size

  fig = plt.figure(frameon=False)
  fig.set_size_inches(w/500, h/500)
  ax = plt.Axes(fig, [0., 0., 1., 1.])
  ax.set_axis_off()
  fig.add_axes(ax)

  bm = Basemap(llcrnrlon=minlon,
               llcrnrlat=minlat,
               urcrnrlon=maxlon,
               urcrnrlat=maxlat,
               lat_0=(minlat+maxlat)/2,
               lon_0=(minlon+maxlon)/2,
               projection="tmerc", resolution=None)
  bm.imshow(image, aspect='equal', origin='upper')
  bm.plot(loc["lon"], loc["lat"], linewidth=1,color='r', latlon=True)
  bm.plot(loc["lon"][0], loc["lat"][0], 'go', latlon=True)
  fig.savefig(name, dpi=500)

def main():
  f = h5py.File(sys.argv[1], 'a')
  loc = f["loc0"][:]
  saveMap(loc, sys.argv[1].replace(".h5", "_map.png"))
  f.close()

main()


