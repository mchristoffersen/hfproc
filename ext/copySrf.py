import h5py
import sys

srcf = h5py.File(sys.argv[1], 'r')
dstf = h5py.File(sys.argv[2], 'a')

srcf.copy("ext/srf0", dstf["ext"])

srcf.close()
dstf.close()
