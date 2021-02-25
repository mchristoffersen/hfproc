import logging as log, sys, argparse, os
from multiprocessing import Pool
import h5py

###
dt = -437
###


def shift(fname):
    log.info("Shifting " + fname + " by " + str(dt) + "s")
    fd = h5py.File(fname, "a")
    time0 = fd["raw"]["time0"][:]
    for i in range(len(time0)):
        time0[i][0] += dt

    fd["raw"]["time0"][:] = time0
    fd.close()

    return 0


def main():
    # Set up CLI
    parser = argparse.ArgumentParser(description="Apply a time shift to /raw/time0")
    parser.add_argument("data", help="Data file(s)", nargs="+")
    parser.add_argument(
        "-n",
        "--num-proc",
        type=int,
        help="Number of simultaneous processes, default 1",
        default=1,
    )
    args = parser.parse_args()

    # Set up logging
    log.basicConfig(
        filename=os.path.dirname(args.data[0]) + "/timeShift.log",
        format="%(levelname)s:%(process)d:%(message)s    %(asctime)s",
        level=log.INFO,
    )

    # Print warning and error to stderr
    sh = log.StreamHandler()
    sh.setLevel(log.WARNING)
    sh.setFormatter(log.Formatter("%(levelname)s:%(process)d:%(message)s"))
    log.getLogger("").addHandler(sh)

    # Some initial info
    log.info("Starting time shifting")
    log.info("num_proc %s", args.num_proc)
    log.info("data %s", args.data)

    p = Pool(args.num_proc)
    p.map(shift, args.data)
    p.close()
    p.join()

    return 0


if __name__ == "__main__":
    main()
