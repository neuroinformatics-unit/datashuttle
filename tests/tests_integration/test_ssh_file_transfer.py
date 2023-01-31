"""
# Still need to do more of this.
# 4) test all, in particular the removal of --ignore-existing. When the user transfers, it makes
#    sense to have a comment explicitly stating the nature of the transfer (or, at the end).

# https://stackoverflow.com/questions/18601828/python-block-network-connections-for-testing-purposes
# but these drop python access to internet NOT entire internet (at least some of them)

# this would work for data_type and all other files. But didn't work well for testing, so just use the files.

# DOING NOW -------------------------------------------------------------------
# DONT FORGET THIS IS SUPPOSE TO TEST OVER SSH
# ASK ALEX ABOUT SSH TO CEPH
# how to handle this, because this should be tested as a normal file transfer without SSH. Maybe call these extended
# tests, and test with SSH only if set!
# manualyl check this test is doing what I think it is and check all edge cases
"""

import os
from pathlib import Path
import shutil

import pandas as pd
import pytest
import test_utils
from test_file_conflicts_pathtable import get_pathtable
import getpass
import copy
import builtins
from datashuttle.utils import rclone, ssh

REMOTE_PATH = Path(r"/nfs/nhome/live/jziminski/scratch/datashuttle tests")
REMOTE_HOST_ID = "ssh.swc.ucl.ac.uk"
REMOTE_HOST_USERNAME = "jziminski"
SSH_TEST_FILESYSTEM_PATH = Path("S:/scratch/datashuttle tests")
TEST_SSH = True
# TODO: a trick here, check all files through mounted but actually transfer
# through SSH

class TestFileTransfer:

    @pytest.fixture(scope="module", params=[False, pytest.param(True, marks=pytest.mark.skipif(TEST_SSH is False,  reason="False"))])  # TODO: transfer here both ssh and non-ssh. Only do SSH if some pyetst setting set.
    def pathtable_and_project(self, request, tmpdir_factory ):
        """
        Create a project with default configs loaded.
        This makes a fresh project for each function,
        saved in the appdir path for platform independent
        and to avoid path setup on new machine.

        Ensure change dir at end of session otherwise it
        is not possible to delete project.
        """
        testing_ssh = request.param
        tmp_path = tmpdir_factory.mktemp("test")

        if testing_ssh:
            base_path = SSH_TEST_FILESYSTEM_PATH
        else:
            base_path = tmp_path / "test with space"

        test_project_name = "test_file_conflicts"
        project, cwd = test_utils.setup_project_fixture(
            base_path, test_project_name
        )

        # ssh stuff - move to new function as also used in ssh_setup
        if testing_ssh:
            project.update_config(
                "remote_path",
                test_utils.make_test_path(REMOTE_PATH, test_project_name, "remote")
            )
            project.update_config("remote_host_id", REMOTE_HOST_ID)  # TODO: NEW FUNCTION
            project.update_config("remote_host_username", REMOTE_HOST_USERNAME)
            project.update_config("connection_method", "ssh")

            rclone.setup_remote_as_rclone_target(
                "ssh",
                project.cfg,
                project.cfg.get_rclone_config_name("ssh"),
                project.cfg.ssh_key_path,
            )

            self.setup_hostkeys(project)
            getpass.getpass = lambda _: self.get_password()  # type: ignore   #NEW FUNCTION
            ssh.setup_ssh_key(project.cfg, log=False,)

        pathtable = get_pathtable(project.cfg["local_path"])

        # Make and transfer all files in the pathtable,
        # then upload a subset according to the passed arguments
        self.create_all_pathtable_files(pathtable)

        project.testing_ssh = testing_ssh
        yield [pathtable, project]

        test_utils.teardown_project(cwd, project)

        if testing_ssh:
            for result in SSH_TEST_FILESYSTEM_PATH.glob("*"):
                shutil.rmtree(result)

    # to move start
    def get_password(self):  # TODO: move to utils
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

    # to move end

    # ---------------------------------------------------------------------------------------------------------------
    # Test Rclone File Overwrite
    # ---------------------------------------------------------------------------------------------------------------

    def remote_from_local(self, path_):
        return Path(str(path_).replace("local", "remote"))

    # ---------------------------------------------------------------------------------------------------------------
    # Test File Transfer - All Options
    # ---------------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("sub_names", [
            ["all"],
            ["all_sub"],
            ["all_non_sub"],
            ["sub-001"],
            ["sub-003_date-20231901"],
            ["sub-002", "all_non_sub"],
        ])
    @pytest.mark.parametrize("ses_names", [
        ["all"],
        ["all_ses"],
        ["all_non_ses"],
        ["ses_002"],
        ["all_non_ses", "ses-001"],
    ])
    @pytest.mark.parametrize("data_type", [
        ["all"],
        ["all_ses_level_non_data_type"],
        ["all_data_type"],
        ["behav"],
        ["ephys"],
        ["histology"],
        ["funcimg"],
        ["histology", "behav", "all_ses_level_non_data_type"],
    ])
    def test_all_data_transfer_options(
        self, pathtable_and_project, sub_names, ses_names, data_type
    ):
        """ """
        pathtable, project = pathtable_and_project

        project.upload_data(sub_names, ses_names, data_type)

        # Parse the arguments to filter the pathtable, getting
        # the files expected to be transferred pased on the arguments
        # Note files in sub/ses/datatype folders must be handled
        # separately to those in non-sub, non-ses, non-data-type folders
        sub_names = self.parse_arguments(pathtable, sub_names, "sub")
        ses_names = self.parse_arguments(pathtable, ses_names, "ses")
        data_type = self.parse_arguments(pathtable, data_type, "data_type")

        (
            sub_ses_dtype_arguments,
            extra_arguments,
        ) = self.make_pathtable_search_filter(sub_names, ses_names, data_type)

        data_type_folders = self.query_table(
            pathtable, sub_ses_dtype_arguments
        )
        extra_folders = self.query_table(pathtable, extra_arguments)

        expected_paths = pd.concat([data_type_folders, extra_folders])
        expected_paths = expected_paths.drop_duplicates(subset="path")

        remote_base_paths = expected_paths.base_dir.map(
            lambda x: str(x).replace("local", "remote")
        )
        expected_transferred_paths = remote_base_paths / expected_paths.path

        # Check what paths were actually moved, and test
        path_to_search = self.remote_from_local(project.cfg["local_path"])
        all_transferred = path_to_search.glob("**/*")
        paths_to_transferred_files = filter(Path.is_file, all_transferred)

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

        shutil.rmtree(self.remote_from_local(project.cfg["local_path"]))

    # ---------------------------------------------------------------------------------------------------------------
    # Utils
    # ---------------------------------------------------------------------------------------------------------------

    def query_table(self, pathtable, arguments):
        if any(arguments):
            folders = pathtable.query(" | ".join(arguments))
        else:
            folders = pd.DataFrame()
        return folders

    def parse_arguments(self, pathtable, list_of_names, field):
        # field - "sub", "ses", or "data_type"
        if list_of_names in [["all"], [f"all_{field}"]]:
            entries = pathtable.query(f"parent_{field} != False")[
                f"parent_{field}"
            ]
            entries = list(set(entries))
            if list_of_names == ["all"]:
                entries += (
                    [f"all_non_{field}"]
                    if field != "data_type"
                    else ["all_ses_level_non_data_type"]
                )
            list_of_names = entries
        return list_of_names

    def create_all_pathtable_files(self, pathtable):
        """"""
        for i in range(pathtable.shape[0]):
            filepath = pathtable["base_dir"][i] / pathtable["path"][i]
            filepath.parents[0].mkdir(parents=True, exist_ok=True)
            test_utils.write_file(filepath, contents="test_entry")

    def make_pathtable_search_filter(self, sub_names, ses_names, data_type):
        """ """
        sub_ses_dtype_arguments = []
        extra_arguments = []

        for sub in sub_names:

            if sub == "all_non_sub":
                extra_arguments += ["is_non_sub == True"]
            else:
                if "histology" in data_type:
                    sub_ses_dtype_arguments += [
                        f"(parent_sub == '{sub}' & (parent_data_type == 'histology' | parent_data_type == 'histology'))"
                    ]

                for ses in ses_names:

                    if ses == "all_non_ses":
                        extra_arguments += [
                            f"(parent_sub == '{sub}' & is_non_ses == True)"
                        ]
                    else:

                        for dtype in data_type:
                            if dtype == "all_ses_level_non_data_type":
                                extra_arguments += [
                                    f"(parent_sub == '{sub}' & parent_ses == '{ses}' & is_ses_level_non_data_type == True)"
                                ]
                            else:
                                sub_ses_dtype_arguments += [
                                    f"(parent_sub == '{sub}' & parent_ses == '{ses}' & (parent_data_type == '{dtype}' | parent_data_type == '{dtype}'))"
                                ]

        return sub_ses_dtype_arguments, extra_arguments
