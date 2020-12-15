def ddVerify(dd):
  # Function to verify data dictionaries built from raw data files before transformation to hdf5
  allK = ["sig", "stack", "spt", "ntrace", "trlen", "fs", "rx0", "lat", "lon", "alt", "tfull", "tfrac"]
  chirpK = ["txCF", "txBW", "txlen", "txPRF"]
  impK = ["txCF", "txPRF"]

  ddK = dd.keys()

  err = 0

  # Make sure that sig is present and has a valid value, then add correct keys
  if("sig" not in ddK):
  	print("Missing: sig")
  	return 1

  if(dd["sig"] not in ["chirp", "impulse"]):
  	print("Invalid sig value")
  	return 1

  if(dd["sig"] == "chirp"):
  	allK += chirpK
  else:
  	allK += impK

  # Look for extra keys
  for key in ddK:
  	if(key not in allK):
  		print("Extra: " + key)
  		err = 1

  # look for missing keys
  for key in allK:
  	if(key not in ddK):
  		print("Missing: " + key)
  		err = 1

  return err



