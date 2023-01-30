# Things to test

# test SSH
# ---------------------------------------------------------------------
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
# mock pushing from two separate places and merging into single project

# TODO: need to be on the VPN. So we can't CI this test.

# TODO: these can be tested as
# TODO: test search_ssh_remote_for_directories
# TODO: get_list_of_directory_names_over_sftp


import builtins
import copy
import getpass
import os

import paramiko
import pytest
import test_utils

from datashuttle.utils import rclone, ssh

# Specify the SSH configurations to use to connect. The password
# should be stored in a file called test_ssh_password.txt located
# in the same directory as test_ssh.py

REMOTE_PATH = r"/nfs/nhome/live/jziminski/manager/project_manager_tests"
REMOTE_HOST_ID = "ssh.swc.ucl.ac.uk"
REMOTE_HOST_USERNAME = "jziminski"


@pytest.mark.skip(
    reason="SSH tests require SWC VPC. " "These cannot be run using CI"
)
class TestSSH:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """
        Make a project as per usual, but now add
        in test ssh configurations
        """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_ssh"
        project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )

        project.update_config(
            "remote_path",
            REMOTE_PATH,
        )
        project.update_config("remote_host_id", REMOTE_HOST_ID)
        project.update_config("remote_host_username", REMOTE_HOST_USERNAME)
        project.update_config("connection_method", "ssh")

        rclone.setup_remote_as_rclone_target(
            "ssh",
            project.cfg,
            project.cfg.get_rclone_config_name("ssh"),
            project.cfg.ssh_key_path,
        )

        yield project
        test_utils.teardown_project(cwd, project)

    # -----------------------------------------------------------------
    # Utils
    # -----------------------------------------------------------------

    def get_password(self):
        """
        Load the password from file. Password is provided to NIU team
        members only.
        """
        test_ssh_script_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            test_ssh_script_path + "/test_ssh_password.txt", "r"
        ) as file:
            password = file.readlines()[0]
        return password

    def setup_mock_input(self, input_):
        """
        This is very similar to pytest monkeypatch but
        using that was giving me very strange output,
        monkeypatch.setattr('builtins.input', lambda _: "n")
        i.e. pdb went deep into some unrelated code stack
        """
        orig_builtin = copy.deepcopy(builtins.input)
        builtins.input = lambda _: input_  # type: ignore
        return orig_builtin

    def restore_mock_input(self, orig_builtin):
        """
        orig_builtin: the copied, original builtins.input
        """
        builtins.input = orig_builtin

    def setup_hostkeys(self, project):
        """
        Convenience function to verify the server hostkey.
        """
        orig_builtin = self.setup_mock_input(input_="y")
        ssh.verify_ssh_remote_host(
            project.cfg["remote_host_id"], project.cfg.hostkeys_path, log=True
        )
        self.restore_mock_input(orig_builtin)

    # -----------------------------------------------------------------
    # Test Setup SSH Connection
    # -----------------------------------------------------------------

    @pytest.mark.parametrize("input_", ["n", "o", "@"])
    def test_verify_ssh_remote_host_do_not_accept(
        self, capsys, project, input_
    ):
        """
        Use the main function to test this. Test the sub-function
        when accepting, because this main function will also
        call setup ssh key pairs which we don't want to do yet

        This should only accept for "y" so try some random strings
        including "n" and check they all do not make the connection.
        """
        orig_builtin = self.setup_mock_input(input_)

        project.setup_ssh_connection_to_remote_server()

        self.restore_mock_input(orig_builtin)

        captured = capsys.readouterr()

        assert "Host not accepted. No connection made.\n" in captured.out

    def test_verify_ssh_remote_host_accept(self, capsys, project):
        """
        User is asked to accept the server hostkey. Mock this here
        and check hostkey is successfully accepted and written to configs.
        """
        test_utils.clear_capsys(capsys)
        orig_builtin = self.setup_mock_input(input_="y")

        verified = ssh.verify_ssh_remote_host(
            project.cfg["remote_host_id"], project.cfg.hostkeys_path, log=True
        )

        self.restore_mock_input(orig_builtin)

        assert verified
        captured = capsys.readouterr()
        assert captured.out == "Host accepted.\n"

        with open(project.cfg.hostkeys_path, "r") as file:
            hostkey = file.readlines()[0]

        assert f"{project.cfg['remote_host_id']} ssh-ed25519 " in hostkey

    def test_generate_and_write_ssh_key(self, project):
        """
        Check ssh key for passwordless connection is written
        to file
        """
        path_to_save = project.cfg["local_path"] / "test"
        ssh.generate_and_write_ssh_key(path_to_save)

        with open(path_to_save, "r") as file:
            first_line = file.readlines()[0]

        assert first_line == "-----BEGIN RSA PRIVATE KEY-----\n"

    def test_setup_ssh_key_success(
        self, project, capsys
    ):  # TODO: need to be on the VPN. So we can't CI this test.
        """
        Setup Hostkeys again. This is required for setting up SSH keys. It is
        required to enter the password once to setup ssh key pair. Check
        when password is enterd the key pair is made sucessfully.

        Then, try to connect and check this works without password.
        """
        self.setup_hostkeys(project)

        getpass.getpass = lambda _: self.get_password()  # type: ignore
        ssh.setup_ssh_key(
            project.cfg.ssh_key_path,
            project.cfg.hostkeys_path,
            project.cfg,
            log=False,
        )

        assert (
            f"Host accepted.\n"
            f"Connection to {project.cfg['remote_host_id']} made successfully."
            f"\nSSH key pair setup successfully. "
            f"Private key at:" in capsys.readouterr().out
        )

        test_utils.clear_capsys(capsys)
        with paramiko.SSHClient() as client:
            ssh.connect_client(
                client,
                project.cfg,
                project.cfg.hostkeys_path,
                ssh_key_path=project.cfg.ssh_key_path,
            )

        assert (
            capsys.readouterr().out
            == f"Connection to {project.cfg['remote_host_id']} made successfully.\n"
        )

    def test_setup_ssh_key_failure(self, project):
        """
        Enter the wrong password and check failure is gracefully handled
        """
        self.setup_hostkeys(project)

        getpass.getpass = lambda _: "wrong_password"  # type: ignore

        with pytest.raises(BaseException) as e:
            ssh.setup_ssh_key(
                project.cfg.ssh_key_path,
                project.cfg.hostkeys_path,
                project.cfg,
                log=False,
            )

        assert (
            "Could not connect to server. Ensure that "
            "\n1) You have run setup_ssh_connection_to_remote_server() "
            "\n2) You are on VPN network if required. "
            "\n3) The remote_host_id:" in str(e.value)
        )
