# Signal processing utilities #

import logging as log
import numpy as np
import sys
import scipy

def arangeT(start, stop, fs):
	"""Generate a time vector from start to stop, sampled at frequency fs.
	The time vector will be generated on the closed interval [start, stop]
	The start, stop, and sampling frequency args must have the same time units

	Keyword arguments:
	start -- Start time
	stop -- Stop time
	fs -- Sampling frequency
	"""
	if(stop < start):
		msg = "stop time is less than start time: start(%f) stop(%f)" % (start, stop)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	if(stop == start):
		msg = "stop time can not equal stop time: %f" % (start)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	if(fs <= 0):
		msg = "sampling frequency must be positive: %f" % (fs)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	nsamp = int((stop-start)*fs)
	dt = 1.0/fs
	seq = start + dt*np.arange(nsamp+1, dtype=np.float64)

	return seq


def pulseCompress(sig, ref, axis=0):
	"""Perform a pulse compression (circular cross-correlation) of the columns or
	rows of 2D array "sig" with the 1D array "ref"

	Keyword arguments:
	sig -- 2D array to pulse compress
	ref -- 1D reference signal
	axis -- Axis along which to pulse compress, 0 is columns and 1 is rows
	"""
	if(sig.ndim != 2):
		msg = "sig must be two dimensional: %f" % (sig.ndim)
		error(sys._getframe().f_code.co_name, TypeError, msg)

	if(ref.ndim != 1):
		msg = "ref must be one dimensional: %f" % (ref.ndim)
		error(sys._getframe().f_code.co_name, TypeError, msg)

	if(sig.shape[axis] < len(ref)):
		msg = "ref must be shorter than or equal to sig pulse compression axis: ref(%f) sig(%f)" % (len(ref), sig.shape[axis])
		error(sys._getframe().f_code.co_name, TypeError, msg)

	if(axis not in [0,1]):
		msg = "axis must be one of [0,1]: %f" % (axis)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	# Zero pad reference signal
	c = np.append(ref, np.zeros(sig.shape[axis] - len(ref)))

	C = np.conj(np.fft.fft(c))
	PC = np.fft.fft(sig, axis=axis)

	if(axis == 0): # cols
		PC = PC * C[:, None]
	elif(axis == 1): # rows
		PC = PC*C[None, :]

	pc = np.fft.ifft(PC, axis=axis)

	return pc


def arangeN(nsamp, fs):
	"""Generate a time vector with nsamp samples at sampling frequency fs

	Keyword arguments:
	nsamp -- Number of samples
	fs -- Sampling frequency
	"""	
	if(nsamp <= 0):
		msg = "number of samples must be positive: %f" % (nsamp)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	if(fs <= 0):
		msg = "sampling frequency must be positive: %f" % (fs)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	if(axis not in [0,1]):
		msg = "axis must be one of [0,1]: %f" % (axis)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	dt = 1.0/fs
	seq = np.arange(nsamp, dtype=np.float64)*dt

	return seq


def baseband(sig, cf, fs, axis=0):
	"""Mix the rows or colums of sig with the frequency cf in order to "baseband" them
	such that cf is shifted to zero frequency. The "cf" and "fs" arguments must have the
	same units.

	Keyword arguments:
	sig -- 2D array to baseband the rows or columns of
	cf -- Frequency to shift to zero frequency
	fs -- Sampling frequency of sig along the axis to be basebanded
	axis -- axis to baseband, 0 is columns and 1 is rows
	"""
	if(sig.ndim != 2):
		msg = "sig must be two dimensional: %f" % (sig.ndim)
		error(sys._getframe().f_code.co_name, TypeError, msg)
	
	if(fs <= 0):
		msg = "sampling frequency must be positive: %f" % (fs)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	if(axis not in [0,1]):
		msg = "axis must be one of [0,1]: %f" % (axis)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	# If sig is a real signal get the analytic signal
	if(not np.iscomplexobj(sig)):
		sig = scipy.signal.hilbert(sig, axis=axis)

	# Baseband traces to the frequency cf
	i = np.complex(0, 1)
	t = arangeN(sig.shape[axis], fs)
	fb = np.exp(2 * np.pi * i * -cf * t)

	if(axis == 0):
		sig = sig * fb[:, None]
	elif(axis == 1):
		sig = sig * fb[None, :]

	return sig


def baseChirp(tdur, bw, fs):
	"""Generate a flat envelope linear chirp centered at 0 frequency. All args
	must use the same time unit.

	Keyword arguments:
	tlen -- Time duration
	bw -- bandwidth of the chirp in the same units as fs
	fs -- sampling frequency
	"""
	if(tlen <= 0):
		msg = "chirp duration must be positive: %f" % (fs)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	if(fs <= 0):
		msg = "sampling frequency must be positive: %f" % (fs)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	i = np.complex(0, 1)
	t = arangeT(0, tdur, fs)
	fstart = -0.5*bw
	b = bw/tlen
	c = np.exp(2 * np.pi * i * (0.5 * b * np.square(t) + fstart * t))

	return c


def findOutgoDT(sig, axis=0):
	"""Find outgoing wave location in each row or column of rx0 using the time derivative.
	The first sample with a gradient exceeding the standard deviation of the gradients in
	that row or column is marked for each trace. The mode is reported.

	Keyword arguments:
	sig -- 2D array to find ougoing wave in
	axis -- Axis to find outgoing wave along
	"""
	if(sig.ndim != 2):
		msg = "sig must be two dimensional: %f" % (sig.ndim)
		error(sys._getframe().f_code.co_name, TypeError, msg)
	
	if(axis not in [0,1]):
		msg = "axis must be one of [0,1]: %f" % (axis)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	dSig = np.gradient(sig, axis=axis)

	std = np.std(dSig)

	argmx = np.argmax(dSig > std, axis=axis)

	return scipy.stats.mode(argmx).mode[0]


def findOutgoPC(sig, ref, axis=0):
	"""Find the outgoing wave location using pulse compression. Pulse compress along
	the rows or columns of sig and then take the max value of each row or column to be
	the outgoing wave. Report the mode.

	Keyword arguments:
	sig -- Basebanded 2D array to find the outgoing wave in
	ref -- Basebanded reference chirp
	"""
	if(sig.ndim != 2):
		msg = "sig must be two dimensional: %f" % (sig.ndim)
		error(sys._getframe().f_code.co_name, TypeError, msg)

	if(ref.ndim != 1):
		msg = "ref must be one dimensional: %f" % (ref.ndim)
		error(sys._getframe().f_code.co_name, TypeError, msg)

	if(axis not in [0,1]):
		msg = "axis must be one of [0,1]: %f" % (axis)
		error(sys._getframe().f_code.co_name, ValueError, msg)

	# Pulse compress and get peak loc
	sig = np.roll(sig, sig.shape[axis]//2, axis=axis) # Roll in case peak is before time 0
	rx0 = pulseCompress(sig, ref)
	argmx = np.argmax(np.abs(sig), axis=axis)

	return scipy.stats.mode(argmx).mode[0] - (rx0.shape[axis]//2)

