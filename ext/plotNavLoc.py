import h5py
import matplotlib.pyplot as plt
import sys

f = h5py.File(sys.argv[1], "r")

nav = f["ext"]["nav0"]
loc = f["raw"]["loc0"]

plt.plot(nav["lat"], nav["lon"], ".", loc["lat"], loc["lon"], ".")
plt.legend(["Nav", "Loc"])
plt.show()
