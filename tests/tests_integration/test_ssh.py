# Things to test

# test SSH
# ---------------------------------------------------------------------
# test setup ssh
#       show server key
#       write ssh key pair
#       connect without password
# full transfer tests (similar as to already exists) across SSH
# test switching between local and SSH, as this caused a bug previously

# test realistic file transfer
# ---------------------------------------------------------------------
# make a full fake directory containing all data types
# test transferring it over SSH and a locally mounted drive (ceph)
# test a) all data transfers, hard coded, lots of combinations
#      b) test what happens when internet looses conenctions
#      c) test what happens when files change

# more file transfer tests
# ---------------------------------------------------------------------
# generate files in the folders, test what happens when attempting to overwrite a file
#
