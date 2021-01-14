import h5py
import numpy as np
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import rasterio as rio
import pyproj


def genMap(bmap, loc, name):
    navsys = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

    trkX, trkY = pyproj.transform(navsys, bmap.crs, loc["lon"], loc["lat"])

    gt = ~bmap.transform
    ix, iy = gt * (trkX, trkY)

    bounds = [int(min(ix)), int(max(ix)), int(min(iy)), int(max(iy))]

    w = bounds[1] - bounds[0]
    h = bounds[3] - bounds[2]

    print(w, h)
    bounds[0] -= 50
    bounds[1] += 50
    bounds[2] -= 50
    bounds[3] += 50

    rowSub = (bounds[2], bounds[3] + 1)
    colSub = (bounds[0], bounds[1] + 1)
    print(rowSub, colSub)
    win = rio.windows.Window.from_slices(rowSub, colSub)

    r = bmap.read(1, window=win)
    g = bmap.read(2, window=win)
    b = bmap.read(3, window=win)

    bmdata = np.dstack((r, g, b))

    print("heyy")

    fig = plt.figure(frameon=False)
    fig.set_size_inches(w / 5, h / 5)
    plt.imshow(bmdata, extent=bounds, aspect="equal")
    plt.plot(ix, iy, "r-", linewidth=2)
    plt.plot(ix[0], iy[0], "go")
    plt.axis("off")
    print("hi")
    plt.savefig(name, dpi=5, bbox_inches="tight", pad_inches=0)
    plt.show()
    return


def main():
    f = h5py.File(sys.argv[1], "a")
    bmap = rio.open(sys.argv[2], mode="r")
    loc = f["raw"]["loc0"][:]
    genMap(bmap, loc, sys.argv[1].replace(".h5", "_map.png"))
    f.close()


main()
