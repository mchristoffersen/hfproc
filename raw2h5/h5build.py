# HDF5 builder - takes in dd dict and filename
import h5py
import numpy as np
from ddVerify import ddVerify
import logging as log
import os.path


def generateChirp(cf, bw, length, fs):
    if cf == -1 or bw == -1 or length == -1 or fs == -1:
        return [0]

    initFreq = cf - (cf * bw / 200)
    freqSlope = (cf * bw / 100) / length
    nsamp = int(length * fs)
    t = np.linspace(0, length - 1.0 / fs, nsamp)

    c = np.zeros((nsamp, 1))
    for i in range(nsamp):
        c[i] = np.cos(
            -np.pi / 2 + 2 * np.pi * (initFreq + (freqSlope / 2) * t[i]) * t[i]
        )

    return c


def h5build(dd, outf):
    # Verify data dictionary contents
    if ddVerify(dd):
        log.error("Invalid data dict " + os.path.basename(outf))
        return 1

    if os.path.isfile(outf):
        log.error("HDF5 file already exists " + outf)
        return 1

    try:
        fd = h5py.File(outf, "w")
    except:
        log.error("Unable to open HDF5 file for writing " + outf)
        return 1

    string_t = h5py.string_dtype(encoding='ascii')

    # Create group structure
    # |-raw
    # |-drv
    # |  |-pick
    # |-ext

    raw = fd.create_group("raw")
    drv = fd.create_group("drv")
    pick = drv.create_group("pick")
    ext = fd.create_group("ext")

    description_attr = "Data as recorded by the radar with minimal processing."
    raw.attrs.create("description", description_attr, dtype=string_t)

    description_attr = "External (to the radar) data to aid interpretation of radar data"
    ext.attrs.create("description", description_attr, dtype=string_t)

    description_attr = "Data products derived from data in the raw and/or drv groups."
    drv.attrs.create("description", description_attr, dtype=string_t)

    description_attr = "Glacier bed pick data"
    pick.attrs.create("description", description_attr, dtype=string_t)

    # Root attrs
    if(dd["sig"] == "chirp"):
        fd.attrs.create("institution", "University of Arizona", dtype=string_t)
        fd.attrs.create("instrument", "Arizona Radio-Echo Sounder (ARES)", dtype=string_t)
        description_attr = "Radar data acquired by the University of Arizona's Arizona Radio-Echo Sounder (ARES) instrument over glaciers in Alaska. Data and important metadata are provided in HDF5 files, browse products are provided as PNG formatted images."
        fd.attrs.create("description", description_attr, dtype=string_t)
    elif(dd["sig"] == "impulse"):
        fd.attrs.create("institution", "University of Alaska Fairbanks", dtype=string_t)
        fd.attrs.create("instrument", "University of Alaska Fairbanks High Frequency Radar Sounder (UAF HF)", dtype=string_t)
        description_attr = "Radar data acquired by the University of Alaska Fairbanks High Frequency Radar Sounder (UAF HF) instrument over glaciers in Alaska. Data and important metadata are provided in HDF5 files, browse products are provided as PNG formatted images."
        fd.attrs.create("description", description_attr, dtype=string_t)
    else:
        log.error("Invalid signal type for root metadata selection")
        return 1

    # rx0 dataset
    rx0 = raw.create_dataset(
        "rx0",
        data=dd["rx0"],
        dtype=np.float32,
        compression="gzip",
        compression_opts=9,
        shuffle=True,
        fletcher32=True,
    )


    fs_attr = np.array([(dd["fs"], "hertz")], dtype=[("value","u4"),("unit",string_t)])
    rx0.attrs.create("samplingFrequency", fs_attr[0], dtype=fs_attr.dtype)

    description_attr = """Raw data acquired by the radar. The fast time axis (columns) is two way travel time from the airplane. The data values have not been altered after quantization by the receiver and as such do not have physical units."""
    rx0.attrs.create("description", description_attr, dtype=string_t)

    trlen_attr = np.array([(dd["trlen"],"second")], dtype=[("value","f8"),("unit",string_t)])
    rx0.attrs.create("traceLength", trlen_attr[0], dtype=trlen_attr.dtype)

    rx0.attrs.create("stacking", dd["stack"], dtype=np.uint64)
    rx0.attrs.create("samplesPerTrace", dd["spt"], dtype=np.uint64)
    rx0.attrs.create("numTrace", dd["ntrace"], dtype=np.uint64)

    if dd["sig"] == "chirp":
        # ref chirp
        chirp = generateChirp(dd["txCF"], dd["txBW"], dd["txlen"], dd["fs"])
        ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
        ch[0 : len(chirp)] = chirp

        # tx0 dataset
        tx0 = raw.create_dataset("tx0", data=ch, dtype=np.float32)
        tx0.attrs.create("signal", "chirp", dtype=string_t)

        txbw_attr = np.array([(dd["txBW"],"percent of center frequency")], dtype=[("value","f8"),("unit",string_t)])
        tx0.attrs.create("bandwidth", txbw_attr[0], dtype=txbw_attr.dtype)
        
        txlen_attr = np.array([(dd["txlen"],"second")], dtype=[("value","f8"),("unit",string_t)])
        tx0.attrs.create("length", txlen_attr[0], dtype=txlen_attr.dtype)

    elif dd["sig"] == "tone":
        # ref tone
        tone = generateChirp(dd["txCF"], 0, dd["txlen"], dd["fs"])
        ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
        ch[0 : len(tone)] = tone

        # tx0 dataset
        tx0 = raw.create_dataset("tx0", data=ch, dtype=np.float32)
        tx0.attrs.create("signal", "tone", string_t)

        txlen_attr = np.array([(dd["txlen"],"second")], dtype=[("value","f8"),("unit",string_t)])
        tx0.attrs.create("length", txlen_attr[0], dtype=txlen_attr.dtype)

    elif dd["sig"] == "impulse":
        # ref impulse, zeros for now
        # tone = generateChirp(dd["txCF"], 0, dd["txlen"], dd["fs"])
        ch = np.zeros((dd["rx0"].shape[0], 1)).astype("float32")
        # ch[0:len(tone)] = tone

        # tx0 dataset
        tx0 = raw.create_dataset("tx0", data=ch, dtype=np.float32)
        tx0.attrs.create("signal", "impulse", string_t)


    else:
        print("Unknown signal type")
        sys.exit()

    # Universal tx0 attributes
    txcf_attr = np.array([(dd["txCF"],"hertz")], dtype=[("value","f8"),("unit",string_t)])
    tx0.attrs.create("centerFrequency", txcf_attr[0], dtype=txcf_attr.dtype)

    txprf_attr = np.array([(dd["txPRF"], "hertz")], dtype=[("value","f8"),("unit",string_t)])
    tx0.attrs.create("pulseRepetitionFrequency", txprf_attr[0], dtype=txprf_attr.dtype)

    description_attr = """Information about the transmitted signal."""
    tx0.attrs.create("description", description_attr, dtype=string_t)

    # loc dataset
    loc_t = np.dtype([("lat", np.float32), ("lon", np.float32), ("hgt", np.float32)])
    locList = [None] * dd["ntrace"]
    for i in range(dd["ntrace"]):
        locList[i] = (dd["lat"][i], dd["lon"][i], dd["alt"][i])

    locList = np.array(locList, dtype=loc_t)
    loc0 = raw.create_dataset("loc0", data=locList, dtype=loc_t)

    description_attr = """GPS position log from the radar - lower quality than /ext/nav0 position."""
    loc0.attrs.create("description", description_attr, dtype=string_t)

    loc0.attrs.create("CRS", np.string_("WGS84"))

    # time dataset
    time_t = np.dtype([("fullS", np.uint64), ("fracS", np.float64)])
    timeList = [None] * dd["ntrace"]
    for i in range(dd["ntrace"]):
        timeList[i] = (dd["tfull"][i], dd["tfrac"][i])
    timeList = np.array(timeList, dtype=time_t)
    time0 = raw.create_dataset("time0", data=timeList, dtype=time_t)
    description_attr = """Time tag for each trace in the raw data."""
    time0.attrs.create("description", description_attr, dtype=string_t)

    time0.attrs.create("unit", "second", dtype=string_t)
    time0.attrs.create("clock", "UTC seconds since midnight on 1 Jan 1970", dtype=string_t)

    fd.close()

    return 0
