import h5py
import numpy as np
import argparse, os
import logging as log
import scipy.signal as spsig
from multiprocessing.pool import Pool
import matplotlib.pyplot as plt

def sar(fn):
	try:
		f = h5py.File(fn, "r+")
	except:
		log.error("Unable to open " + fn)
		return 1

	# Unfocused sar for flat interfaces
	proc0 = f["drv"]["proc0"][:]
	#proc0 = proc0[:,15000:20000]
	f.close()

	#plt.imshow(np.log(np.abs(proc0)))
	#plt.show()

	#plt.plot(np.fft.fftfreq(proc0.shape[1], 1.0/20),np.fft.fft(proc0[1275,:]))
	#plt.show()
	w = 100
	s = 1

	nsart = int((proc0.shape[1]-w)/s)

	sar = np.zeros((proc0.shape[0], nsart), dtype=np.complex64)

	#sos = spsig.butter(10, .1, btype="low", fs=20, output="sos")
	for i in range(nsart):
		startWin = i*s
		stopWin = i*s+w

		frame = proc0[:, startWin:stopWin]

		#frame = spsig.sosfilt(sos, frame, axis=1)
		FRAME = np.fft.fft(frame, axis=1)
		#plt.imshow(np.abs(FRAME), aspect="auto")
		#plt.show()
		f = np.fft.fftfreq(frame.shape[1], 1.0/20)
		DOPSEL = FRAME[:,np.abs(f)<=.0]
		#plt.imshow(np.abs(DOPSEL), aspect="auto")
		#plt.show()
		sar[:,i] = np.sum(np.abs(DOPSEL), axis=1)
		#sar[:,i] = #np.sum(frame, axis=1)
		print(i)

	f = h5py.File(fn, "r+")

	del f["drv/sar0"]
	sar0 = f["drv"].require_dataset(
		"sar0",
		shape=sar.shape,
		dtype=np.complex64,
		compression="gzip",
		compression_opts=9,
		shuffle=True,
		fletcher32=True,
	)
	sar0[:] = sar.astype(np.complex64)
	f.close()

	return 0

def main():
	# Set up CLI
	parser = argparse.ArgumentParser(
		description="Program for unfocused SAR processing of HDF5 files"
	)
	parser.add_argument("data", help="Data file(s)", nargs="+")
	parser.add_argument(
		"-n",
		"--num-proc",
		type=int,
		help="Number of simultaneous processes, default 1",
		default=1,
	)
	args = parser.parse_args()

	# Set up logging - stick in directory with first data file
	log.basicConfig(
		filename=os.path.dirname(args.data[0]) + "/upc.log",
		format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
		level=log.INFO,
	)

	# Print warning and error to stderr
	sh = log.StreamHandler()
	sh.setLevel(log.WARNING)
	sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
	log.getLogger("").addHandler(sh)

	log.info("Starting sar script")
	log.info("num_proc %s", args.num_proc)
	log.info("data %s", args.data)

	p = Pool(args.num_proc)
	p.map(sar, args.data)
	p.close()
	p.join()

	return 0

main()