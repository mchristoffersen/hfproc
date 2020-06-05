import sys, struct, h5py
import numpy as np
from h5build import h5build

def parseRaw(fname):
  fd = open(fname, 'rb')
  data = fd.read()
  nb = len(data)

  if(data[0:4] != bytes.fromhex("d0d0beef")):
    return -1

  dd = {}

  dd["version"] = struct.unpack('f', data[4:8])[0]

  if(dd["version"] == 1.0):
    hdr = struct.unpack("ifdddddddi", data[0:68])
   
    dd["chirpCF"] = hdr[2]
    dd["chirpBW"] = hdr[3]/100
    dd["chirpLen"] = hdr[4]
    dd["chirpAmp"] = hdr[5]
    dd["chirpPRF"] = hdr[6]
    dd["traceLen"] = hdr[7]
    dd["fs"] = int(hdr[8])
    dd["stack"] = hdr[9]
    dd["spt"] = int(dd["traceLen"]*dd["fs"])
    dd["ntrace"] = int((nb - 68)/(56 + dd["spt"]*4));
    dd["rx0"] = np.zeros((dd["spt"], dd["ntrace"])).astype("float")
    dd["lat"] = np.zeros(dd["ntrace"]).astype("float")
    dd["lon"] = np.zeros(dd["ntrace"]).astype("float")
    dd["alt"] = np.zeros(dd["ntrace"]).astype("float")
    dd["dop"] = np.zeros(dd["ntrace"]).astype("float")
    dd["nsat"] = np.zeros(dd["ntrace"]).astype("int32")
    dd["tfull"] = np.zeros(dd["ntrace"]).astype("int64")
    dd["tfrac"] = np.zeros(dd["ntrace"]).astype("double")

    for i in range(dd["ntrace"]):
      ofst = 68 + ((56 + dd["spt"]*4)*i)
      fix = struct.unpack("qqdqffffIi", data[ofst:ofst+56])
      dd["tfull"][i] = fix[1]
      dd["tfrac"][i] = fix[2]
      dd["lat"][i] = fix[4]
      dd["lon"][i] = fix[5]
      dd["alt"][i] = fix[6]
      dd["dop"][i] = fix[7]
      dd["nsat"][i] = fix[8]

      dd["rx0"][:,i] = struct.unpack('f'*dd["spt"], data[ofst+56:ofst+56+dd["spt"]*4])
  
  dd["rx0"] = np.array(dd["rx0"]).astype(np.float32)
  # Circular shift to correct for xmit delay in Ettus hardware
  dd["rx0"] = np.roll(dd["rx0"], -105, axis=0)

  return dd

def main():
  dd = parseRaw(sys.argv[1])
  if(dd == -1):
    print("Invalid lowres data file")
    exit()
  outf = sys.argv[2] + '/' + sys.argv[1].split('/')[-1].replace(".dat",".h5")
  print(outf)

  # Open file
  fd = h5py.File(outf, "w")

  h5build(dd, fd)

  # Some basic info at file root
  fd.attrs.create("Info", np.string_("Data acquired by the University of Arizona Long Wavelength Radio Echo Sounder (LoWRES) radar system"))
  fd.close()

main()
