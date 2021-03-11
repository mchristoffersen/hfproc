import sys, h5py, scipy.io
import numpy as np
import scipy.signal as spsig
import scipy.stats as spstat
from scipy.stats import mode
from scipy.signal import hilbert
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os.path
import pandas as pd
import logging as log

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


def baseChirp(tlen, cf, bw, fs):
    # Function to generate a linear basebanded chirp
    # Amplitude of 1, flat window

    i = np.complex(0, 1)
    t = arangeT(0, tlen, fs)
    fstart = -(0.5 * cf * bw)
    b = (cf * bw) / tlen

    c = np.exp(2 * np.pi * i * (0.5 * b * np.square(t) + fstart * t))

    return c


def findOffsetDT(rx0):
    # Find offset with time derivative.
    # Calc gradient along trace
    grd = np.gradient(rx0, axis=0)

    # Std dev
    std = np.std(grd)

    # Find first slope that is greater than 1 std from mean slope
    argmx = np.argmax(grd > std, axis=0)

    return mode(argmx).mode[0]


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

    return mode(argmx).mode[0] - (rx0.shape[0] // 2)



def parseRaw(fname):
    dd = {}
    fn = fname.split("/")[-1]

    try:
        fd = scipy.io.loadmat(fname)
    except:
        log.warning("Failed to load mat file " + fn)
        return -1

    log.debug("Loaded mat file " + fn)

    # Open matching signal info file and get info
    year = fname.split("/")[-1][0:4]
    cols = ["name", "sig", "cf", "bw", "len"]
    meta = os.path.dirname(fname) + "/" + year + "meta.csv"
    if not os.path.isfile(meta):
        log.warning("Metadata file does not exist " + meta)

    df = pd.read_csv(meta, names=cols)
    log.debug("Loaded metadata file " + meta)
    name = os.path.basename(fname).replace(".mat", "")
    nfo = df[df["name"] == name].reset_index()
    if len(nfo) != 1:
        log.error("Can't find metadata for " + fn)
        return -1

    log.debug("Applied metadata from " + meta)

    # Ingest data from rec struct
    ch0 = fd["rec"]["ch0"][0][0]
    lat = fd["rec"]["lat"][0][0][0]
    lon = fd["rec"]["lon"][0][0][0]
    elev = fd["rec"]["ele"][0][0][0]
    time = fd["rec"]["time"][0][0][0]
    time = pd.to_datetime(time - 719529, unit="D")  # Convert matlab to unix epoch
    dt = fd["rec"]["dt"][0][0][0][0]

    dd["rx0"] = np.transpose(ch0).astype(np.float32)

    dd["ntrace"] = dd["rx0"].shape[1]

    dd["lat"] = lat.astype(np.float32)
    dd["lon"] = lon.astype(np.float32)
    dd["alt"] = elev.astype(np.float32)

    dd["tfull"] = np.zeros(dd["ntrace"]).astype(np.uint64)
    dd["tfrac"] = np.zeros(dd["ntrace"]).astype(np.float64)

    dd["sig"] = nfo["sig"][0]

    if dd["sig"] == "chirp":
        dd["txCF"] = nfo["cf"][0]
        dd["txBW"] = nfo["bw"][0] / 100.0
        dd["txlen"] = nfo["len"][0]
        dd["txPRF"] = 2000
    elif dd["sig"] == "tone":
         log.warning("Not converting tone file " + fname)
         return -1 
#        dd["txCF"] = nfo["cf"][0]
#        dd["txlen"] = -1
#        dd["txPRF"] = -1
    elif dd["sig"] == "impulse":
        dd["txCF"] = 2e6
        dd["txPRF"] = 1000

    dd["fs"] = 1.0 / dt
    dd["stack"] = 100
    dd["spt"] = dd["rx0"].shape[0]
    dd["trlen"] = dt * dd["spt"]

    # Set right TAI to UTC offset
    date = time[0]
    if(date.year > 2016):
        taio = 37
    elif(date.year == 2016):
        taio = 36
    elif(date.year == 2015):
        if(date.month > 6):
            taio = 36
        else:
            taio = 35
    elif(date.year in [2013, 2014]):
        taio = 35
    else:
        log.warning("No TAI to UTC offset found for " + fn)

    # Deal with duplicate times
    timen = np.zeros(len(time))
    for i in range(dd["ntrace"]):
        timen[i] = time[i].value / 10e8 - taio

    uniq, idx = np.unique(timen, return_index=True)
    x = np.array(range(len(timen)))
    timen = np.interp(x, idx, uniq)

    for i in range(dd["ntrace"]):
        dd["tfull"][i] = int(timen[i])
        dd["tfrac"][i] = timen[i] - int(timen[i])

    # Handle offset changes over 2015, 2016, 2017 campaigns
    date = datetime.utcfromtimestamp(dd["tfull"][0])
    ofcorr = np.nan
    
    # 2013
    if date.year == 2013:
        ofst = findOffsetDT(dd["rx0"])
        ofcorr = -ofst

    # 2014 May
    elif date.year == 2014 and date.month == 5:
        ofst = findOffsetDT(dd["rx0"])
        ofcorr = -ofst

    # 2014 Aug
    elif date.year == 2014 and date.month == 8:
        ofst = findOffsetDT(dd["rx0"])
        ofcorr = -ofst

    # 2015 May
    elif date.year == 2015 and date.month == 5:
        if dd["sig"] == "impulse":
            if date.day <= 17:
                ofcorr = -347
            elif date.day == 19 and date.hour == 22 and date.minute <= 34:
                ofcorr = -147
            else:
                ofcorr = -172
        elif dd["sig"] == "chirp":
            ofcorr = -537

    # 2015 Aug
    elif date.year == 2015 and date.month == 8:
        if dd["sig"] == "impulse":
            ofcorr = -347
        elif dd["sig"] == "chirp":
            ofcorr = -393

    # 2016 May
    elif(date.year == 2016 and date.month == 5):
      if(dd["sig"] == "impulse"):
        ofst = findOffsetDT(dd["rx0"])
        ofcorr = -ofst
      elif(dd["sig"] == "chirp"):
        refchirp = baseChirp(dd["txlen"], dd["txCF"], dd["txBW"], dd["fs"])
        ofst = findOffsetPC(dd["rx0"], refchirp, dd["txCF"], dd["fs"])
        ofcorr = -ofst

    # 2016 Aug
    elif(date.year == 2016 and date.month == 8):
      if(dd["sig"] == "impulse"):
        ofcorr = -325
      elif(dd["sig"] == "chirp"):
        refchirp = baseChirp(dd["txlen"], dd["txCF"], dd["txBW"], dd["fs"])
        ofst = findOffsetPC(dd["rx0"], refchirp, dd["txCF"], dd["fs"])
        ofcorr = -ofst

    # 2017 May
    elif date.year == 2017 and date.month == 5:
        ofcorr = -571

    elif date.year == 2017 and date.month == 8:
        if date.day <= 16:
            ofcorr = -370
        elif date.day == 22:
            ofcorr = -477
        elif date.day > 22:
            ofcorr = -364

    if not np.isnan(ofcorr):
        dd["rx0"] = np.roll(dd["rx0"], ofcorr, axis=0)
    else:
        log.warning("No offset correction found for " + fn)

    dd["institution"] = "University of Alaska Fairbanks"
    dd["instrument"] = "University of Alaska Fairbanks High Frequency Radar Sounder (UAF HF)"

    return dd
