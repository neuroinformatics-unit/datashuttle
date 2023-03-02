from pathlib import Path
from types import SimpleNamespace

import pytest


def pytest_configure(config):
    pytest.ssh_config = SimpleNamespace(
        TEST_SSH=True,
        PASSWORD_FILE="/home/joe/test_pass.txt", # r"C:\Users\Joe\temp_pass.txt",  # don't store this on github!
        USERNAME="jziminski",
        REMOTE_HOST_ID="hpc-gw1.hpc.swc.ucl.ac.uk",
        FILESYSTEM_PATH=Path("/home/joe/ceph_mount/neuroinformatics/scratch/datashuttle_tests/fake_data",
        ),  # FILESYSTEM_PATH and SERVER_PATH these must point to the same folder on the HPC, filesystem
        SERVER_PATH=Path(
            r"/ceph/neuroinformatics/neuroinformatics/scratch/datashuttle_tests/fake_data"
        ),  # as a moutned drive and server as the linux path to connect through SSH
    )
