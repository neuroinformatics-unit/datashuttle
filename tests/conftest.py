"""
Test configs, used for setting up SSH tests.

Before running these tests, it is necessary to setup
an SSH key. This can be done through datashuttle
ssh.setup_ssh_key(project.cfg, log=False).

Store this path somewhere outside of the test environment,
and it will be copied to the project test folder before testing.

FILESYSTEM_PATH and SERVER_PATH these must point
to the same folder on the HPC, filesystem,
as a mounted drive and server as the linux path to
connect through SSH
"""
import platform
from types import SimpleNamespace
from pathlib import Path
import pytest
import test_utils

test_ssh = True
username = "joeziminski"  # "jziminski"
remote_host_id = "localhost"  # "hpc-gw1.hpc.swc.ucl.ac.uk"

if platform.system() == "Windows":
    ssh_key_path = r"/Users/joeziminski/git_repos/datashuttle/tests/tests_integration"  # automate
else:
    ssh_key_path = r"/Users/joeziminski/git_repos/datashuttle/tests/tests_integration"

def pytest_configure(config):
    pytest.ssh_config = SimpleNamespace(
        TEST_SSH=test_ssh,
        SSH_KEY_PATH=ssh_key_path,
        USERNAME=username,
        REMOTE_HOST_ID=remote_host_id,
        FILESYSTEM_PATH= str(Path.home() / ".datashuttle_tests"),  # FILESYSTEM_PATH and SERVER_PATH these must point to the same folder on the HPC, filesystem
        SERVER_PATH= str(Path.home() / ".datashuttle_tests"),  # as a mounted drive and server as the linux path to connect through SSH
    )
    test_utils.set_datashuttle_loggers(disable=True)
