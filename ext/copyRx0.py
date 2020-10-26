import h5py
import sys

srcf = h5py.File(sys.argv[1], 'r')
dstf = h5py.File(sys.argv[2], 'a')

#srcf.copy("ext/srf0", dstf["ext"])
print(sys.argv[2].split('/')[-1])
dstf["raw"]["rx0"][:] = srcf["raw"]["rx0"][:]

srcf.close()
dstf.close()
