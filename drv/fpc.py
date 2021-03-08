import matplotlib.pyplot as plt
import numpy as np
import argparse, os, sys
import logging as log
from multiprocessing.pool import Pool
import h5py
import pyproj as prj

def arangeT(start, stop, fs):
	# Function to generate set of
	# Args are start time, stop time, sampling frequency
	# Generates times within the closed interval [start, stop] at 1/fs spacing
	# Double precision floating point

	# Slow way to do this, but probably fine for the homework
	seq = np.array([]).astype(np.double)
	c = start
	while c <= stop:
		seq = np.append(seq, c)
		c += 1.0 / fs

	return seq

def baseChirp(tlen, cf, bw, fs):
	# Function to generate a linear basebanded chirp
	# Amplitude of 1, flat window

	i = np.complex(0, 1)
	t = arangeT(0, tlen, fs)
	fstart = -(0.5 * cf * bw)
	b = (cf * bw) / tlen

	c = np.exp(2 * np.pi * i * (0.5 * b * np.square(t) + fstart * t))

	return c


def rayTime(xi, plane, subgl, nadElev, slope, n1 = 1, n2 = 1.78):
	c = 299792458

	yelev = nadElev + (xi-plane[0])*np.tan(np.radians(slope))
	ta = (n1*np.sqrt((plane[0]-xi)**2 + (plane[1] - yelev)**2))/c
	ti = (n2*np.sqrt((subgl[0]-xi)**2 + (subgl[1] - yelev)**2))/c
	t = 2*(ta+ti)

	return t, yelev

def rayPath(plane, subgl, nadElev, slope, n1 = 1, n2 = 1.78):
	# Gradient descent to find the shortest raypath
	# Input:
	#	plane - (x, y) - location of plane
	#   subgl - (x, y) - location of point reflector
	# 	nadElev - elevation of surface below the plane
	#	slope - slope of ground along track degrees
	#	n1 - Index of refraction of top layer
	# 	n2 - Index of refraction of bottom layer

	x = plane[0]
	step = 10
	c = 0
	while step >= 1e-2:
		c += 1
		if(c >= 50e3):
			print("plane", plane)
			print("subgl", subgl)
			print("nadElev", nadElev)
			print("slope", slope)
			return -1
		xar = np.array([x-step, x, x+step])
		t, y = rayTime(xar, plane, subgl, nadElev, slope)
		if(t[0] > t[1] and t[2] > t[1]): # If min is bounded
		#	print("bounded")
			step = step/10
			continue
		if(t[0] > t[1] and t[1] > t[2]):
		#	print("->")
			x = x + step
			continue
		if(t[0] < t[1] and t[1] < t[2]):
		#	print("<-")
			x = x - step
			continue


	return t[1], [x, y[1]]

def snellCheck(plane, subgl, iface, slope, n1 = 1, n2 = 1.78):
	# Incident vector
	iv = [plane[0]-iface[0], plane[1]-iface[1]]

	# Transmitted vector
	tv = [iface[0]-subgl[0], iface[1]-subgl[1]]

	ia = np.degrees(np.arctan(iv[0]/iv[1])) + slope
	ta = np.degrees(np.arctan(tv[0]/tv[1])) + slope
	print(ia, ta)

	dsnell = n1*np.sin(np.radians(ia)) - n2*np.sin(np.radians(ta))

	if(dsnell > 1e-4):
		return False

	return True


def dopplerFreq(plane, subgl, iface, slope, v, wv = 120, n1 = 1, n2 = 1.78):
	# Incident vector
	iv = [plane[0]-iface[0], plane[1]-iface[1]]

	# Transmitted vector
	tv = [iface[0]-subgl[0], iface[1]-subgl[1]]

	ia = np.arctan(iv[0]/iv[1])
	ta = np.arctan(tv[0]/tv[1])

	psi = np.radians(slope)
	fd = (2*v/wv)*(np.cos(iv)*(np.tan(iv)-np.tan(iv-psi)) + n2*np.cos(tv)*np.tan(tv-psi))
	
	return fd


def sar(fn):
	c = 299792458
	try:
		f = h5py.File(fn, "r+")
	except Exception as e:
		log.error("Unable to open " + fn)
		log.error(e)
		return 1

	pc0 = f["drv"]["proc0"][:]
	nav0 = f["ext"]["nav0"][:]
	srf0 = f["ext"]["srf0"][:]
	prf = f["raw"]["tx0"].attrs["pulseRepetitionFrequency"]
	cf = f["raw"]["tx0"].attrs["centerFrequency"]
	bw = f["raw"]["tx0"].attrs["bandwidth"]
	tlen = f["raw"]["tx0"].attrs["length"]
	fs = f["raw"]["rx0"].attrs["samplingFrequency"]
	stack = f["raw"]["rx0"].attrs["stacking"]
	f.close()

	# Get chirp autocorrelation
	chirp = baseChirp(tlen, cf, bw, fs)
	chirp = chirp*np.hanning(len(chirp))

	chirp = np.append(chirp, np.zeros(pc0.shape[0] - len(chirp)))

	# Autocorrelation of the chirp
	aChirp = np.fft.ifft(np.fft.fft(chirp)*np.conj(np.fft.fft(chirp)))

	tps = prf/stack

	lle = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
	xyz = "+proj=geocent +ellps=WGS84 +no_defs"

	pLat = [lat for (lat, lon, elev) in nav0]
	pLon = [lon for (lat, lon, elev) in nav0]
	pElev = [elev for (lat, lon, elev) in nav0]

	xform = prj.Transformer.from_crs(lle, xyz)
	px, py, pz = xform.transform(pLon, pLat, pElev)

	# Velocity
	vx = np.gradient(px)*tps
	vy = np.gradient(py)*tps
	vz = np.gradient(pz)*tps
	v = np.sqrt(vx**2 + vy**2 + vz**2)

	# Along track distance
	atX = np.zeros(len(px))
	xStep = np.zeros(len(px))
	for i in range(1,len(px)):
		dx = px[i]-px[i-1]
		dy = py[i]-py[i-1]
		dz = pz[i]-pz[i-1]
		xStep[i] = np.sqrt(dx**2 + dy**2 + dz**2)
		atX[i] = atX[i-1] + xStep[i]


	## Focus a test chunk
	# Get representative trajectory 
	#chunkStart = 5800
	#chunkStop = 7000
	#midStart = 6500
	#midstop = 6601



	# Frame size
	fSize = 51 # 5 seconds of samples
	# loop over frames, do sar
	rstart = 5800
	rstop = 7000
	foc = np.zeros((pc0.shape[0], rstop-rstart-fSize)).astype(np.complex64)
	fidx = 0
	for i in range(5800,7000-fSize,10):
		# Get surface points, fit line to calculate surface slope
		fSrf = srf0[i:i+fSize]
		fAtX = atX[i:i+fSize]
		fPz = pElev[i:i+fSize]
		frame = pc0[:,i:i+fSize]

		A = np.ones((len(fSrf), 2))
		A[:,0] = fAtX
		
		x, res, rank, sing = np.linalg.lstsq(A, fSrf, rcond=None)

		psi = np.degrees(np.arctan(x[0]))

		midPz = fPz[fSize//2]
		midSrfZ = fSrf[fSize//2]
		midAtX = fAtX[fSize//2]
		midSrfSamp = int(((2*(midPz-midSrfZ))/c)*fs)
		rayTimes = np.zeros(len(fSrf))

		# In each frame iterate over depth samples to focus returns
		# at each range
		stopSamp = min(pc0.shape[0], midSrfSamp+1600)
		frameRMC = np.zeros_like(frame)
		frameCorr = np.zeros_like(frame)
		sarTrace = np.zeros(pc0.shape[0]).astype(np.complex64)
		for s in range(midSrfSamp, stopSamp):
			print(s)
			dz = (s-midSrfSamp)*(1/fs)*(c/1.78)/2
			for i,pLoc in enumerate(zip(fAtX, fPz)):
				rayTimes[i], iface = rayPath(pLoc, [midAtX, midSrfZ-dz], fSrf[i], psi)


			rSamp = (rayTimes*fs).astype(np.int32)
			dSamp = rSamp - rSamp[fSize//2]

			rayPhase = np.exp(-1*1j*2*np.pi*cf*rayTimes)
			dPhase = rayPhase - rayPhase[fSize//2]
			plt.plot(fAtX, np.abs(dPhase)/np.pi)
			plt.show()

			for j in range(frame.shape[1]):
				frameCorr[:,j] = np.roll(aChirp, dSamp[j]+s)*np.exp(1j*dPhase[j])

			sarTrace[s] = np.sum(np.multiply(frameCorr, frame))

			#plt.imshow(np.log(np.abs(frameCorr)), aspect="auto")
			#plt.show()

			#plt.plot(np.abs(frameCorr[:,50]))
			#plt.show()

			# Range migration correction
			#for j in range(frame.shape[1]):
			#	frameRMC[:,j] = np.roll(frame[:,j], -1*dSamp[j])

			#sarTrace[s] = np.sum(frameRMC[s,:] * np.exp(-1j*dPhase))

			#if(not s%200):
			#	plt.plot(np.abs(sarTrace)/np.max(np.abs(sarTrace)))
			#	plt.plot(np.abs(frame[:,fSize//2])/np.max(np.abs(frame[:,fSize//2])))
			#	plt.show()

		foc[:,fidx] = sarTrace
		fidx+=1
		plt.imshow(np.log(np.abs(foc[:,:fidx]+.0001)), aspect="auto")
		#plt.plot(np.abs(frame[:,fSize//2]))
		plt.show()

	return 


def main():
	# Set up CLI
	parser = argparse.ArgumentParser(
		description="Program for focused SAR processing of HDF5 files"
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
		filename=os.path.dirname(args.data[0]) + "/fpc.log",
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

	sar(args.data[0])
	#p = Pool(args.num_proc)
	#p.map(sar, args.data)
	#p.close()
	#p.join()

	return 0

main()


