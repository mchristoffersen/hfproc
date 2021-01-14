import h5py
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import argparse
import logging as log
from multiprocessing import Pool
from scipy.stats import mode
from scipy.signal import hilbert


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


def findOffsetPC(rx0, refchirp, cf, fs):
    # Find offset
    # Analytic signal
    rx0 = hilbert(rx0, axis=0)

    # Baseband it
    rx0 = baseband(rx0, cf, fs)

    # Cross correlate with avg trace, get peak loc
    rx0 = np.roll(rx0, rx0.shape[0] // 2, axis=0)
    rx0 = pulseCompress(rx0, refchirp)
    argmx = np.argmax(np.abs(rx0), axis=0)
    rx0 = np.roll(rx0, -1 * rx0.shape[0] // 2, axis=0)

    return [rx0, (mode(argmx).mode[0] - rx0.shape[0] // 2)]


def findOffsetDT(rx0):
    # Find offset with time derivative.
    # Calc gradient along trace
    grd = np.gradient(rx0, axis=0)

    # Find max slope of each trace
    argmx = np.argmax(grd, axis=0)

    return mode(argmx).mode[0]


def saveImageOffset(data, fs, name, offset):
    tbnd = 20e-6  # 20 microseconds
    data = data[0 : int(fs * tbnd), :]
    fig = plt.figure(frameon=False)
    data = np.abs(data) + sys.float_info.epsilon
    im = np.log(data ** 2)
    plt.imshow(
        im,
        aspect="auto",
        cmap="Greys_r",
        vmin=np.percentile(im, 60),
        vmax=np.percentile(im, 99.5),
    )
    plt.axhline(y=offset, color="r", linestyle="-")
    # plt.show()
    plt.title(str(offset))
    fig.savefig(name, dpi=500)
    plt.close()

    return 0


def baseChirp(tlen, cf, bw, fs):
    # Function to generate a linear basebanded chirp
    # Amplitude of 1, flat window

    i = np.complex(0, 1)
    t = arangeT(0, tlen, fs)
    fstart = -(0.5 * cf * bw)
    b = (cf * bw) / tlen

    c = np.exp(2 * np.pi * i * (0.5 * b * np.square(t) + fstart * t))

    return c


def genQlook(fname, outd):
    f = h5py.File(fname, "r")
    sig = f["raw"]["tx0"].attrs["signal"]
    print(sig.decode())

    if sig == b"impulse":
        rx0 = f["raw"]["rx0"][:]
        cf = f["raw"]["tx0"].attrs["centerFrequency"]
        fs = f["raw"]["rx0"].attrs["samplingFrequency"]
        shift = findOffsetDT(rx0)

    elif sig == b"chirp":
        rx0 = f["raw"]["rx0"][:]
        cf = f["raw"]["tx0"].attrs["centerFrequency"]
        bw = f["raw"]["tx0"].attrs["bandwidth"]
        tl = f["raw"]["tx0"].attrs["length"]
        fs = f["raw"]["rx0"].attrs["samplingFrequency"]

        refchirp = baseChirp(3e-6, cf, bw, fs)
        print(tl, cf, bw, fs)
        plt.plot(rx0[:, 1000])
        plt.show()
        rx0, shift = findOffsetPC(rx0, refchirp, cf, fs)

    # Find hardware delay with outgoing wave

    if rx0.shape[1] < 20:
        exit()
    saveImageOffset(
        rx0, fs, outd + "/" + fname.split("/")[-1].replace(".h5", "_shiftDT.png"), shift
    )
    f.close()

    return 0


def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program creating quicklook images of /drv/proc0"
    )
    parser.add_argument("dest", help="Output directory")
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
        filename=os.path.dirname(args.dest) + "/genDataQlook.log",
        format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
        level=log.INFO,
    )

    # Print warning and error to stderr
    sh = log.StreamHandler()
    sh.setLevel(log.WARNING)
    sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
    log.getLogger("").addHandler(sh)

    log.info("Starting data and clutter quicklook generation")
    log.info("num_proc %s", args.num_proc)
    log.info("dest %s", args.dest)
    log.info("data %s", args.data)

    # Do conversion
    outd = [args.dest] * len(args.data)

    p = Pool(args.num_proc)
    p.starmap(genQlook, zip(args.data, outd))
    p.close()
    p.join()


main()
