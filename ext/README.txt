lidar fresnel zone surface elevation extraction. 
together this set of code indexes into available lidar files to generate a database 
of which radar tracks line up with which lidar tracks. lidar files are then sampled along 
the flight track to define the nadir surface elevation as the mean/median lidar elevation
within the radar's first fresnel zone. 
code written by mchristo, some modifications by btober.

-order to run code:
1. buildLASlocindex.py
2. buildLASdb.py
3. fresnelElev.sh
