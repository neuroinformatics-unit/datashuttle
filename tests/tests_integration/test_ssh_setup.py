"""SSH configs are set in conftest.py . The password
should be stored in a file called test_ssh_password.txt located
in the same folder as test_ssh.py.
"""

import pytest
import ssh_test_utils
import test_utils
from pytest import ssh_config

from datashuttle.utils import ssh


@pytest.mark.skipif(ssh_config.TEST_SSH is False, reason="TEST_SSH is false")
class TestSSH:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """Make a project as per usual, but now add
        in test ssh configurations.
        """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_ssh"
        project = test_utils.setup_project_fixture(tmp_path, test_project_name)

        ssh_test_utils.setup_project_for_ssh(
            project,
            ssh_config.FILESYSTEM_PATH,
            ssh_config.CENTRAL_HOST_ID,
            ssh_config.USERNAME,
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
        """Use the main function to test this. Test the sub-function
        when accepting, because this main function will also
        call setup ssh key pairs which we don't want to do yet.

        This should only accept for "y" so try some random strings
        including "n" and check they all do not make the connection.
        """
        orig_builtin = ssh_test_utils.setup_mock_input(input_)

        project.setup_ssh_connection()

        ssh_test_utils.restore_mock_input(orig_builtin)

        captured = capsys.readouterr()

        assert "Host not accepted. No connection made.\n" in captured.out

    def test_verify_ssh_central_host_accept(self, capsys, project):
        """User is asked to accept the server hostkey. Mock this here
        and check hostkey is successfully accepted and written to configs.
        """
        test_utils.clear_capsys(capsys)
        orig_builtin = ssh_test_utils.setup_mock_input(input_="y")

        verified = ssh.verify_ssh_central_host(
            project.cfg["central_host_id"], project.cfg.hostkeys_path, log=True
        )

        ssh_test_utils.restore_mock_input(orig_builtin)

        assert verified
        captured = capsys.readouterr()
        assert captured.out == "Host accepted.\n"

        with open(project.cfg.hostkeys_path) as file:
            hostkey = file.readlines()[0]

        assert f"{project.cfg['central_host_id']} ssh-ed25519 " in hostkey

    def test_generate_and_write_ssh_key(self, project):
        """Check ssh key for passwordless connection is written
        to file.
        """
        path_to_save = project.cfg["local_path"] / "test"
        ssh.generate_and_write_ssh_key(path_to_save)

        with open(path_to_save) as file:
            first_line = file.readlines()[0]

        assert first_line == "-----BEGIN RSA PRIVATE KEY-----\n"
