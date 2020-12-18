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

def keyCheck(fd, refK, group):
	# Check for groups in root
	chkK = fd[group].keys()
	diff = chkLists(refK,chkK)
	if(diff[0]):
		if(diff[0] in [1,3]):
			print(group + " missing: " + str(diff[1]))
		if(diff[0] in [2,3]):
			print(group + " extra: " + str(diff[2]))
		print()
	return diff[0]

def structureCheck(fd):
	## Check that all groups, datasets, and attributes are present

	## Format def
	rootK = ["raw", "drv", "ext"]
	rawK = ["rx0", "tx0", "loc0", "time0"]
	drvK = ["proc0", "clutter0", "pick"]
	extK = ["nav0", "srf0"]
	pickK = ["twtt_surf"]

	s = 0
	s += keyCheck(fd, rootK, '/')
	s += keyCheck(fd, extK, '/ext')

	return s

def main():
	for i in range(len(sys.argv)-1):
		fd = h5py.File(sys.argv[i+1], 'r')
		print(sys.argv[i+1])
		r = structureCheck(fd)
		if(not r):
			print("PASSED\n")
		fd.close()

main()
