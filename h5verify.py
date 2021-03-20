import h5py, sys
import argparse

# Tool to verify HDF5 files, checking for bonus/missing
# groups/datasets/attributes and does some rule checks on
# the data


class h5Struct:
    def __init__(self):
        self.groups = ["raw", "drv", "ext", "drv/pick"]
        self.dsets = [
            "raw/rx0",
            "raw/tx0",
            "raw/loc0",
            "raw/time0",
            "drv/clutter0",
            "drv/proc0",
            "drv/pick/twtt_surf",
            "drv/pick/twtt_bed",
            "drv/pick/thick",
            "ext/nav0",
            "ext/srf0",
            "ext/srf0count"
        ]
        self.attrs = {
            "": ["institution", "instrument", "description"],
            "raw": ["description"],
            "drv": ["description"],
            "ext": ["description"],
            "drv/pick": ["description"],
            "raw/rx0": [
                "numTrace",
                "samplesPerTrace",
                "samplingFrequency",
                "stacking",
                "traceLength",
                "description"
            ],
            "raw/tx0": [
                "signal",
                "centerFrequency",
                "pulseRepetitionFrequency",
                "length",
                "bandwidth",
                "description"
            ],
            "raw/loc0": ["CRS", "description"],
            "raw/time0": ["clock", "unit", "description"],
            "drv/clutter0": ["description"],
            "drv/proc0": ["note", "description"],
            "drv/pick/twtt_surf": ["unit", "description"],
            "drv/pick/twtt_bed": ["unit", "description"],
            "drv/pick/thick": ["unit", "description"],
            "ext/nav0": ["CRS", "description"],
            "ext/srf0": ["verticalDatum", "unit", "description"],
            "ext/srf0count": ["description"]
        }

        # Check that all groups/dsets are in attrs list
        for group in self.groups:
            if group not in self.attrs.keys():
                print("\tAttribute definition missing for:", group)
        for dset in self.dsets:
            if dset not in self.attrs.keys():
                print("\tAttribute definition missing for:", dset)

    def attrChk(self, name, chkAttrs, refAttrs):
        for attr in chkAttrs:
            if attr in refAttrs:
                refAttrs.remove(attr)
            else:
                print("\tInvalid Attribute:", name + "/" + attr)

        return

    def structChk(self, name, item):
        if isinstance(item, h5py.Group):
            if name in self.groups:
                self.groups.remove(name)
            else:
                print("\tInvalid Group:", name)
        elif isinstance(item, h5py.Dataset):
            if name in self.dsets:
                self.dsets.remove(name)
            else:
                print("\tInvalid Dataset:", name)
        chkAttrs = list(item.attrs.keys())
        refAttrs = self.attrs[name]
        self.attrChk(name, chkAttrs, refAttrs)

        return

    def chkRootAttrs(self, fd):
        chkAttrs = list(fd.attrs.keys())
        refAttrs = self.attrs[""]
        self.attrChk("", chkAttrs, refAttrs)

        return

def uniqList(lst):
    # Returns the count of non-unique elements in a list
    for i, e in enumerate(lst):
        lst[i] = tuple(e)
    return len(lst)-len(set(lst))

def main():
    # Set up CLI
    parser = argparse.ArgumentParser(
        description="Program for verification of HDF5 file format and contents"
    )
    parser.add_argument("data", help="Data file(s)", nargs="+")
    # parser.add_argument("-n", "--num-proc", type=int, help="Number of simultaneous processes, default 1", default=1)
    args = parser.parse_args()

    for file in args.data:
        print("File:", file)

        ## Check structure
        vstruct = h5Struct()
        fd = h5py.File(file, "r")
        fd.visititems(vstruct.structChk)
        vstruct.chkRootAttrs(fd)

        for group in vstruct.groups:
            print("\tMissing Group:", group)

        for dset in vstruct.dsets:
            print("\tMissing Dataset:", dset)

        for obj in vstruct.attrs:
            for attr in vstruct.attrs[obj]:
                print("\tMissing Attribute:", obj + "/" + attr)

        ## Check contents

        # ext/nav0 has all unique values
        try:
            nav0 = list(fd["ext/nav0"][:])
            nuniq = uniqList(nav0)
            if(nuniq):
                print("\t" + str(nuniq) + "/" + str(len(nav0)) + "  ext/nav0 values non-unique")
        except KeyError:
            print("\tUnable to upen ext/nav0")

        # raw/time0 has all unique values
        try:
            time0 = list(fd["raw/time0"][:])
            nuniq = uniqList(time0)
            if(nuniq):
                print("\t" + str(nuniq) + "/" + str(len(time0)) + "  raw/time0 values non-unique")
        except KeyError:
            print("\tUnable to upen raw/time0")



        fd.close()
        print("\n")


main()
