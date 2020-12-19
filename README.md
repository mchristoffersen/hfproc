# The hfproc Airborne Sounding Radar Processor

This repo is a set of Python 3 scripts to process chirped and impulse sounding radar data, from a few specific instruments. First converting the raw data files into an HDF5 based format and then subtracting a rolling mean and pulse compressing the data if it is chirped. It also contains modules to use timing information associated with each trace of the radar data to extract navigation data from an GPS trajectory and to extract a radar surface from lidar data by taking the median elevation value of all lidar points in the first fresnel zone of the radar for each trace.
