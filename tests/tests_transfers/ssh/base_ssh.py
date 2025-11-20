""" """

import os
import platform
import subprocess
from pathlib import Path

import pytest

from ..base_transfer import BaseTransfer
from . import ssh_test_utils

# Choose port 3306 for running on GH actions
# suggested in https://github.com/orgs/community/discussions/25550
PORT = 3306
os.environ["DS_SSH_PORT"] = str(PORT)


class BaseSSHTransfer(BaseTransfer):
    """
    Class holding fixtures and methods for testing the
    custom transfers with keys (e.g. all_non_sub).
    """

    @pytest.fixture(
        scope="class",
    )
    def setup_ssh_container(self):
        """
        Set up the Dockerfile container for SSH tests and
        delete it on teardown.
        """
        container_name = "datashuttle_ssh_tests"

        assert ssh_test_utils.docker_is_running(), (
            "docker is not running, "
            "this should be checked at the top of test script"
        )

        image_path = Path(__file__).parent / "ssh_test_images"
        os.chdir(image_path)

        if platform.system() != "Windows":
            build_command = "sudo docker build -t ssh_server ."
            run_command = (
                f"sudo docker run -d -p {PORT}:22 "
                f"--name {container_name} ssh_server"
            )
        else:
            build_command = "docker build -t ssh_server ."
            run_command = f"docker run -d -p {PORT}:22 --name {container_name}  ssh_server"

        build_output = subprocess.run(
            build_command,
            shell=True,
            capture_output=True,
        )
        assert build_output.returncode == 0, (
            f"docker build failed with: STDOUT-{build_output.stdout} "
            f"STDERR-{build_output.stderr}"
        )

        run_output = subprocess.run(
            run_command,
            shell=True,
            capture_output=True,
        )

        assert run_output.returncode == 0, (
            f"docker run failed with: STDOUT-{run_output.stdout} "
            f"STDERR-{run_output.stderr}"
        )

        yield

        subprocess.run(f"docker rm -f {container_name}", shell=True)
