import matplotlib.pyplot as plt
import numpy as np
import argparse, os, sys
import logging as log
from multiprocessing.pool import Pool
import h5py
import pyproj as prj


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
	while step >= 1e-3:
		xar = np.array([x-step, x, x+step])
		t, y = rayTime(xar, plane, subgl, nadElev, slope)
		if(t[0] > t[1] and t[2] > t[1]): # If min is bounded
			step = step/10
			continue
		if(t[0] > t[1] and t[1] > t[2]):
			x = x + step
			continue
		if(t[0] < t[1] and t[1] < t[2]):
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

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def sar(fn):
	try:
		f = h5py.File(fn, "r+")
	except Exception as e:
		log.error("Unable to open " + fn)
		log.error(e)
		return 1

	nav0 = f["ext"]["nav0"][:]
	srf0 = f["ext"]["srf0"][:]
	f.close()

	lle = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
	xyz = "+proj=geocent +ellps=WGS84 +no_defs"

	lat = [lat for (lat, lon, elev) in nav0]
	lon = [lon for (lat, lon, elev) in nav0]
	elev = [elev for (lat, lon, elev) in nav0]

	plt.plot(np.diff(lat))
	plt.show()
	print(lat[0], lon[0], elev[0])

	px, py, pz = prj.transform(
		lle, xyz,
		lon,
		lat,
		elev
	)

	# Velocity
	vx = moving_average(np.gradient(px), n=20)
	vy = moving_average(np.gradient(py), n=20)
	vz = moving_average(np.gradient(pz), n=20)
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

	#plt.plot(vx)
	#plt.plot(vy)
	#plt.plot(vz)
	plt.plot(xStep)
	plt.show()

	return 
	psi = 5 # slope

	# Calculate ray path
	planex = np.arange(21)*5
	planey = 100*np.ones(21)
	srfy = planex*np.tan(np.radians(psi))

	plane = list(zip(planex, planey))

	subgl = [50, -200]

	tl = []
	for i,loc in enumerate(plane):
		t, iface = rayPath(loc, subgl, srfy[i], psi)
		tl.append(t)
		rayx = [loc[0], iface[0], subgl[0]]
		rayy = [loc[1], iface[1], subgl[1]]
		print(snellCheck(loc, subgl, iface, psi))
		plt.plot(rayx, rayy, 'b-')


	#plt.plot(planex, tl)
	#plt.show()

	# Plot it
	#xb = [plane[0], subgl[0]]
	#dx = np.max(xb) - np.min(xb)

	#rayx = [plane[0], iface[0], subgl[0]]
	#rayy = [plane[1], iface[1], subgl[1]]

	plt.gca().set_aspect('equal')
	plt.plot(subgl[0], subgl[1], 'ro')
	#plt.plot(plane[0], plane[1], 'ro')
	plt.plot(planex, srfy, 'g-')
	plt.show()

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

	p = Pool(args.num_proc)
	p.map(sar, args.data)
	p.close()
	p.join()

	return 0

main()


