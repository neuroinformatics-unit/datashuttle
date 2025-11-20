import builtins
import copy
import platform

import pytest

from datashuttle.utils import ssh

from ... import test_utils
from . import ssh_test_utils
from .base_ssh import BaseSSHTransfer

TEST_SSH = ssh_test_utils.docker_is_running()


@pytest.mark.skipif(
    platform.system == "Darwin", reason="Docker set up is not robust on macOS."
)
@pytest.mark.skipif(
    not TEST_SSH,
    reason="SSH tests are not run as docker is either not installed, "
    "running or current user is not in the docker group.",
)
class TestSSH(BaseSSHTransfer):
    @pytest.fixture(scope="function")
    def project(test, tmp_path, setup_ssh_container):
        """Set up a project with configs for SSH into
        the test Dockerfile image.
        """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_ssh"

        project = test_utils.setup_project_fixture(tmp_path, test_project_name)

        ssh_test_utils.setup_project_for_ssh(
            project,
        )

        yield project
        test_utils.teardown_project(project)

    # -----------------------------------------------------------------
    # Test Setup SSH Connection
    # -----------------------------------------------------------------

    @pytest.mark.parametrize("input_", ["n", "o", "@"])
    def test_verify_ssh_central_host_do_not_accept(
        self, capsys, project, input_
    ):
        """Test that host not accepted if input is not "y"."""
        orig_builtin = copy.deepcopy(builtins.input)
        builtins.input = lambda _: input_  # type: ignore

        project.setup_ssh_connection()

        builtins.input = orig_builtin

        captured = capsys.readouterr()

        assert "Host not accepted. No connection made.\n" in captured.out

    def test_verify_ssh_central_host_accept(self, capsys, project):
        """User is asked to accept the server hostkey. Mock this here
        and check hostkey is successfully accepted and written to configs.
        """
        test_utils.clear_capsys(capsys)

        verified = ssh_test_utils.setup_ssh_connection(
            project, setup_ssh_key_pair=False
        )

        assert verified
        captured = capsys.readouterr()

        assert captured.out == "Host accepted.\n"

        with open(project.cfg.hostkeys_path) as file:
            hostkey = file.readlines()[0]

        assert (
            f"[{project.cfg['central_host_id']}]:3306 ssh-ed25519 " in hostkey
        )

    def test_generate_and_write_ssh_key(self, project):
        """Check ssh key for passwordless connection is written
        to file.
        """
        path_to_save = project.cfg["local_path"] / "test"
        ssh.generate_and_write_ssh_key(path_to_save)

        with open(path_to_save) as file:
            first_line = file.readlines()[0]

        assert first_line == "-----BEGIN RSA PRIVATE KEY-----\n"
