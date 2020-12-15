import h5py, sys

# Tool to verify HDF5 files, checking for errors

def chkLists(lref, lchk):
	# Check set differences between lref and lchk
	# Returns [status, [items missing from chk], 
	# [extra items in chk]]

	# Status: 0 if check is good
	#         1 if items missing from chk
	#         2 if extra items in chk
	#         3 if both

	rc = list(set(lref) - set(lchk))
	cr = list(set(lchk) - set(lref))

	ostat = 0

	if(len(rc) > 0):
		ostat += 1
	if(len(cr) > 0):
		ostat += 2

	return (ostat, rc, cr)

def structureCheck(fd):
	## Check that all groups, datasets, and attributes are present
	
	## Format def
	# Groups
	rootGRef = ["raw", "drv", "ext"]
	rawGRef = []
	drvGRef = ["pick"]
	extGRef = []
	pickGRef = []

	# Datasets
	rootDSRef = []
	rawDSRef = ["rx0", "tx0", "loc0", "time0"]
	drvDSRef = ["proc0", "clutter0"]
	extDSRef = ""



	# Check for groups in root
	rootg = fd.keys()
	diff = chkLists(rootgRef,rootg)
	if(diff[0]):
		print(diff)
		return diff[0]

	# Check for attrs in root


	return 0

def main():
	fd = h5py.File(sys.argv[1], 'r')
	structureCheck(fd)
	fd.close()

main()