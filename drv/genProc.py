import logging as log, sys, argparse, os
import h5py
import numpy as np
import sys, os
from scipy.signal import hilbert, butter, filtfilt
import matplotlib.pyplot as plt
from datetime import datetime
from multiprocessing import Pool


def pulseCompress(rx0, refchirp):
    if len(rx0.shape) == 1:
        rx0 = np.expand_dims(rx0, 1)

    pc = np.zeros(rx0.shape).astype("float32")
    refchirp = np.append(refchirp, np.zeros(len(rx0) - len(refchirp)))
    C = np.conj(np.fft.fft(refchirp))
    PC = np.fft.fft(rx0, axis=0)
    PC = PC * C[:, None]
    pc = np.fft.ifft(PC, axis=0)

    return pc


def removeSlidingMeanFFT(rx0, sumint):
    # Sumint in interval to avg over for mean removal
    mean = np.zeros(rx0.shape)
    a = np.zeros(rx0.shape[1])
    a[0 : sumint // 2] = 1
    a[rx0.shape[1] - sumint // 2 : rx0.shape[1]] = 1
    A = np.fft.fft(a)

    # Main circular convolution
    for i in range(rx0.shape[0]):
        T = np.fft.fft(rx0[i, :])
        mean[i, :] = np.real(np.fft.ifft(np.multiply(T, A)) / sumint)

    # Handle edges
    mt = np.zeros(rx0.shape[0])
    for i in range(0, sumint):
        mt = np.add(mt, np.divide(rx0[:, i], sumint))

    for i in range(0, sumint // 2):
        mean[:, i] = mt

    mt = np.zeros(rx0.shape[0])
    for i in range(rx0.shape[1] - sumint, rx0.shape[1]):
        mt = np.add(mt, np.divide(rx0[:, i], sumint))

    for i in range(rx0.shape[1] - sumint // 2, rx0.shape[1]):
        mean[:, i] = mt

    rx0NM = np.subtract(rx0, mean)

    return rx0NM


def removeSlidingMean(rx0):
    sumint = 50
    rx0NM = np.zeros(rx0.shape)

    for i in range(rx0.shape[1]):
        mt = np.zeros(rx0.shape[0])

        if i < sumint / 2:
            for j in range(0, sumint):
                mt = np.add(mt, np.divide(rx0[:, j], sumint))
            rx0NM[:, i] = mt  # rx0[:,i] - mt

        elif i > rx0.shape[1] - sumint // 2:
            for j in range(rx0.shape[1] - sumint, rx0.shape[1]):
                mt = np.add(mt, np.divide(rx0[:, j], sumint))
            rx0NM[:, i] = mt  # rx0[:,i] - mt

        else:
            for j in range(i - sumint // 2, i + sumint // 2):
                mt = np.add(mt, np.divide(rx0[:, j], sumint))
            rx0NM[:, i] = mt  # rx0[:,i] - mt

    return rx0NM


def removeMean(rx0):
    rx0NM = np.zeros(rx0.shape)

    mt = np.mean(rx0, axis=1)

    for i in range(rx0.shape[1]):
        rx0NM[:, i] = rx0[:, i] - mt

    return rx0NM


def arangeN(nsamp, fs):
    # Generate an nsamp length array with samples at fs frequency
    seq = np.zeros(nsamp).astype(np.double)
    c = 0

    for i in range(nsamp):
        seq[i] = c
        c += 1.0 / fs

    return seq


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


def findOffsetPC(rx0, refchirp, cf, fs):
    # Find offset
    # Get mean trace
    mt = np.mean(rx0, axis=1)

    # Analytic signal
    mt = hilbert(mt)

    # Baseband it
    mt = baseband(mt, cf, fs)

    # Cross correlate with avg trace, get peak loc
    mt = np.roll(mt, len(mt) // 2)
    mtPC = pulseCompress(mt, refchirp)
    pkLoc = np.argmax(np.abs(mtPC))

    return pkLoc - len(mt) // 2


def findOffsetDT(rx0):
    # Find offset with time derivative.
    # Get mean trace
    mt = np.mean(rx0, axis=1)

    # Gradient
    dmt = np.gradient(mt)

    # Standard deviation
    std = np.std(dmt)

    # Find first place with slope > 1 std dev
    pkLoc = np.argmax(np.abs(dmt) > std)

    return pkLoc


def baseband(sig, cf, fs):
    # Baseband traces to the frequency cf
    i = np.complex(0, 1)
    t = arangeN(sig.shape[0], fs)
    fb = np.exp(2 * np.pi * i * -cf * t)

    if len(sig.shape) > 1 and max(sig.shape) > 1:
        sig = sig * fb[:, None]
    else:
        sig = sig * fb

    return sig


def proc(fn):
    log.info("Processing " + fn)
    string_t = h5py.string_dtype(encoding='ascii')

    try:
        f = h5py.File(fn, "r+")
    except:
        log.error("Unable to open " + fn)
        return 1

    try:
        rx0 = f["raw"]["rx0"][:]
        sig = f["raw"]["tx0"].attrs["signal"]
    except:
        log.error(
            "Cannot open raw/rx0 dataset or sig attr of raw/tx0 dataset " + fshort
        )
        fd.close()
        return 1

    avgw = 250

    fshort = fn.split("/")[-1]
    dt = datetime.utcfromtimestamp(f["raw"]["time0"][0][0])
    secv = (dt - datetime(1970, 1, 1)).total_seconds()

    log.info("Signal type - %s %s", sig, fshort)
    log.info("Removing a %d trace sliding mean %s", avgw, fshort)

    if rx0.shape[1] > avgw:
        rx0 = removeSlidingMeanFFT(rx0, avgw)
    else:
        rx0 = removeMean(rx0)

    if sig == b"impulse":
        # shiftDT = findOffsetDT(rx0)
        # shiftPC = findOffsetPC(rx0, refchirp, cf, fs)
        # print("%s,%s,%d,%d,%d,%d" % (sys.argv[1].split('/')[-1], sig.decode("utf-8"), secv, shiftDT, 0, rx0.shape[1]))

        # Save processed dataset
        pc = rx0

        # Add 470 ns offset for impulse trigger delay and antenna dangle
        nsamp = int(470e-9/(1/f["raw"]["rx0"].attrs["samplingFrequency"][0]))
        pc = np.roll(pc, nsamp, axis=0)

        proc0 = f["drv"].require_dataset(
            "proc0",
            shape=pc.shape,
            dtype=np.complex64,
            compression="gzip",
            compression_opts=9,
            shuffle=True,
            fletcher32=True,
        )
        proc0[:] = pc.astype(np.complex64)
        proc0.attrs.create(
            "note", "Mean removed in sliding %d trace window" % avgw, dtype=string_t
        )

        description_attr = "Processed data derived from /raw/rx0. Processing varies based on transmit signal type.  The fast time axis (along-trace) is two way travel time from the airplane. Each sample is a complex-valued amplitude with the first single precision float (\"r\") being the real component and the second one (\"i\") being the imaginary component. Like the rx0 dataset this dataset does not have physical units."
        proc0.attrs.create("description", description_attr, dtype=string_t)
        
        f.close()

    elif sig == b"chirp":
        cf = f["raw"]["tx0"].attrs["centerFrequency"][0]
        bw = f["raw"]["tx0"].attrs["bandwidth"][0]
        tl = f["raw"]["tx0"].attrs["length"][0]
        fs = f["raw"]["rx0"].attrs["samplingFrequency"][0]

        ### Process data
        # Generate reference chirp
        refchirp = baseChirp(tl, cf, bw, fs)

        # Find hardware delay with outgoing wave
        # shiftDT = findOffsetDT(rx0)
        # shiftPC = findOffsetPC(rx0, refchirp, cf, fs)
        # print("%s,%s,%d,%d,%d,%d" % (sys.argv[1].split('/')[-1], sig.decode("utf-8"), secv, shiftDT, shiftPC, rx0.shape[1]))

        # Analytic signal
        rx0 = hilbert(rx0, axis=0)

        # Baseband the data to chirp center freq
        rx0 = baseband(rx0, cf, fs)

        # Pulse compression
        pc = pulseCompress(rx0, refchirp)

        # Apply filter
        # [b, a] = butter(4, 1e6, btype='lowpass', fs=100e6)
        # pc = filtfilt(b, a, pc, axis=0)

        # Save processed dataset
        proc0 = f["drv"].require_dataset(
            "proc0",
            shape=pc.shape,
            dtype=np.complex64,
            compression="gzip",
            compression_opts=9,
            shuffle=True,
            fletcher32=True,
        )
        proc0[:] = pc.astype(np.complex64)
        # proc0.attrs.create("note", np.string_("Mean removed in sliding {} trace window. Pulse compression with ideal reference chirp, boxcar amplitude window. 1 MHz low pass filter (2 MHz bandwidth) applied.".format(avgw)))
        proc0.attrs.create(
            "note",
            "Mean removed in sliding %d trace window. Pulse compression with ideal reference chirp, boxcar amplitude window." % avgw, dtype=string_t)

        description_attr = "Processed data derived from /raw/rx0. Processing varies based on transmit signal type.  The fast time axis (along-trace) is two way travel time from the airplane. Each sample is a complex-valued amplitude with the first single precision float (\"r\") being the real component and the second one (\"i\") being the imaginary component. Like the rx0 dataset this dataset does not have physical units."
        proc0.attrs.create("description", description_attr, dtype=string_t)

        f.close()

    else:
        log.error("No processing method for %s %s", sig, fshort)
        f.close()
        return 1

    log.info("Processed " + fshort)

    return 0


def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program for rolling mean removal and pulse compression of HDF5 files"
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
        filename=os.path.dirname(args.data[0]) + "/genProc.log",
        format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
        level=log.INFO,
    )

    # Print warning and error to stderr
    sh = log.StreamHandler()
    sh.setLevel(log.WARNING)
    sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
    log.getLogger("").addHandler(sh)

    log.info("Starting genProc script")
    log.info("num_proc %s", args.num_proc)
    log.info("data %s", args.data)

    p = Pool(args.num_proc)
    p.map(proc, args.data)
    p.close()
    p.join()

    return 0


if __name__ == "__main__":
    main()
