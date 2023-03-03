"""
Test configs, used for setting up SSH tests.

Ensure password is not stored on GitHub.

FILESYSTEM_PATH and SERVER_PATH these must point
to the same folder on the HPC, filesystem,
as a moutned drive and server as the linux path to
connect through SSH
"""
import platform
from types import SimpleNamespace

import pytest

test_ssh = False
username = "jziminski"
remote_host_id = "hpc-gw1.hpc.swc.ucl.ac.uk"
server_path = r"/ceph/neuroinformatics/neuroinformatics/scratch/datashuttle_tests/fake_data"


if platform.system() == "Windows":
    password_file = r"C:\Users\Joe\temp_pass.txt"
    filesystem_path = "X:/neuroinformatics/scratch/datashuttle_tests/fake_data"

else:
    password_file = "/home/joe/test_pass.txt"
    filesystem_path = "/home/joe/ceph_mount/neuroinformatics/scratch/datashuttle_tests/fake_data"


def pytest_configure(config):
    pytest.ssh_config = SimpleNamespace(
        TEST_SSH=test_ssh,
        PASSWORD_FILE=password_file,
        USERNAME=username,
        REMOTE_HOST_ID=remote_host_id,
        FILESYSTEM_PATH=filesystem_path,  # FILESYSTEM_PATH and SERVER_PATH these must point to the same folder on the HPC, filesystem
        SERVER_PATH=server_path,  # as a moutned drive and server as the linux path to connect through SSH
    )
