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

import builtins
import copy

import pytest
import test_utils

from datashuttle.utils import rclone, ssh


class TestSSH:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """ """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_ssh"
        project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )

        project.update_config(
            "remote_path",
            r"/nfs/nhome/live/jziminski/manager/project_manager_tests",
        )
        project.update_config("remote_host_id", "ssh.swc.ucl.ac.uk")
        project.update_config("remote_host_username", "jjz33")
        project.update_config("connection_method", "ssh")

        rclone.setup_remote_as_rclone_target(
            "ssh",
            project.cfg,
            project._get_rclone_config_name("ssh"),
            project._ssh_key_path,
        )

        yield project
        test_utils.teardown_project(cwd, project)

    def setup_mock_input(self, input_):
        """
        This is very similar to pytest monkeypatch but
        using that was giving me very strange output,
        monkeypatch.setattr('builtins.input', lambda _: "n")
        i.e. pdb went deep into some unrelated code stack
        """
        orig_builtin = copy.deepcopy(builtins.input)
        builtins.input = lambda _: input_
        return orig_builtin

    def restore_mock_input(self, orig):
        builtins.input = orig

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
        Capturing of input() text does not work as we need to
        monkeypatch
        """
        capsys.readouterr()  # clear capsys.out
        orig_builtin = self.setup_mock_input(input_="y")

        verified = ssh.verify_ssh_remote_host(
            project.cfg["remote_host_id"], project._hostkeys_path, log=True
        )

        self.restore_mock_input(orig_builtin)

        assert verified
        captured = capsys.readouterr()
        assert captured.out == "Host accepted."

    def test_generate_and_write_ssh_key(self, project):
        breakpoint()
        ssh.generate_and_write_ssh_key(project._datashuttle_path)

    # test_generate_and_write_ssh_key
    # test_setup_ssh_key

    # TODO: add_public_key_to_remote_authorized_keys (maybe)

    # TODO: test search_ssh_remote_for_directories
    # TODO: get_list_of_directory_names_over_sftp
