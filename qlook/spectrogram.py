import scipy.signal as spsig
import sys
import matplotlib.pyplot as plt
import h5py
import numpy as np


def spectro(data, dt):
    tr = np.sum(data, axis=1)
    f, t, sxx = spsig.spectrogram(
        tr, fs=1.0 / dt, window="blackmanharris", nperseg=256, noverlap=220
    )

    plt.pcolormesh(t / 1e-6, f / 1e6, sxx, shading="gouraud")
    plt.ylabel("Frequency [MHz]")
    plt.xlabel("Time [usec]")
    plt.show()

    return 0


def main():
    f = h5py.File(sys.argv[1], "r")
    rx0 = f["raw"]["rx0"][:]
    dt = 1.0 / f["raw"]["rx0"].attrs["samplingFrequency"]
    spectro(rx0, dt)
    exit()


main()
