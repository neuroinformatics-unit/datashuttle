"""
These tests check every possible option for file transfer tests.

These are tested over:
1) SSH
2) Local filesystem. This is done with pytest tmp paths
   as there is no difference between actual filesystem
   and locally mounted drive.

1) require working SSH paths and login  to be setup
below and VPN to the server setup. The password for the
USERNAME must be saved in a file test_ssh_password.txt
in the datashuttle/tests/ folder. The SSH connection
configs must be specified in confytest.py


NOTES
-----
full transfer tests (similar as to already exists) across SSH
test switching between local and SSH, as this caused a bug previously

test realistic file transfer
---------------------------------------------------------------------
make a full fake directory containing all data types
test transferring it over SSH and a locally mounted drive (ceph)
test a) all data transfers, hard coded, lots of combinations
     b) test what happens when internet looses conenctions
     c) test what happens when files change

more file transfer tests
---------------------------------------------------------------------

Wishlist
--------
TODO: generate files in the folders, test what happens when attempting to overwrite a file
TODO: mock pushing from two separate places and merging into single project
TODO: finishing making large real dataset
TODO: currently rawdata only tested.

TODOs
-----
# add final tests on checking underscore order, to logs?

TODO: make sure have tested different data type at different level s
TODO: manually check this test is doing what I think it is and check all edge cases
TODO: SSH tests take ages because a) SSH is slower b) need to wait for filesystem to update (ATM 10 s can probably reduce)

TODO: test connection drop https://stackoverflow.com/questions/18601828/python-block-network-connections-for-testing-purposes
      (but these drop python access to internet NOT entire internet (at least some of them))
TODO: test partial file transfer - in this case, it will never be updateD? Is there a way to print warning
      in rclone whendates or filesizes do not match?





"""

import copy
import getpass
import shutil
import time
from pathlib import Path

import pandas as pd
import pytest
import ssh_test_utils
import test_utils
from pytest import ssh_config
from test_file_conflicts_pathtable import get_pathtable

from datashuttle.utils import ssh


class TestFileTransfer:
    @pytest.fixture(
        scope="class",
        params=[  # Set running SSH or local filesystem
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    ssh_config.TEST_SSH is False,
                    reason="TEST_SSH is set to False.",
                ),
            ),
        ],
    )
    def pathtable_and_project(self, request, tmpdir_factory):
        """
        Create a project for SSH testing. Setup
        the project as normal, and switch configs
        to use SSH connection.

        Although SSH is used for transfer, for SSH tests,
        checking the created filepaths is always
        done through the local filesystem for speed
        and convenience. As such, the drive that is
        SSH to must also be mounted and the path
        supplied to the location SSH'd to.

        For speed, create the project once,
        and all files to transfer. Then in the
        test function, the dir are transferred.
        Partial cleanup is done in the test function
        i.e. deleting the remote_path to which the
        items have been transferred. This is acheived
        by using "class" scope.

        pathtable is a convenient way to represent
        file paths for testing against.
        """
        testing_ssh = request.param
        tmp_path = tmpdir_factory.mktemp("test")

        if testing_ssh:
            base_path = ssh_config.FILESYSTEM_PATH
            remote_path = ssh_config.SERVER_PATH
        else:
            base_path = tmp_path / "test with space"
            remote_path = base_path
        test_project_name = "test_file_conflicts"

        project, cwd = test_utils.setup_project_fixture(
            base_path, test_project_name
        )

        if testing_ssh:
            ssh_test_utils.setup_project_for_ssh(
                project,
                test_utils.make_test_path(
                    remote_path, test_project_name, "remote"
                ),
                ssh_config.REMOTE_HOST_ID,
                ssh_config.USERNAME,
            )

            # Initialise the SSH connection
            ssh_test_utils.setup_hostkeys(project)
            getpass.getpass = lambda _: ssh_test_utils.get_password()  # type: ignore
            ssh.setup_ssh_key(
                project.cfg,
                log=False,
            )

        pathtable = get_pathtable(project.cfg["local_path"])
        self.create_all_pathtable_files(pathtable)
        project.testing_ssh = testing_ssh

        yield [pathtable, project]

        test_utils.teardown_project(cwd, project)

        if testing_ssh:
            for result in ssh_config.SSH_TEST_FILESYSTEM_PATH.glob("*"):
                shutil.rmtree(result)

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

    def remote_from_local(self, path_):
        return Path(str(copy.copy(path_)).replace("local", "remote"))

    # -------------------------------------------------------------------------
    # Test File Transfer - All Options
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "sub_names",
        [
            ["all"],
            ["all_sub"],
            ["all_non_sub"],
            ["sub-001"],
            ["sub-003_date-20231901"],
            ["sub-002", "all_non_sub"],
        ],
    )
    @pytest.mark.parametrize(
        "ses_names",
        [
            ["all"],
            ["all_non_ses"],
            ["all_ses"],
            ["ses-001"],
            ["ses-002_random-key"],
            ["all_non_ses", "ses-001"],
        ],
    )
    @pytest.mark.parametrize(
        "data_type",
        [
            ["all"],
            ["all_ses_level_non_data_type"],
            ["all_data_type"],
            ["behav"],
            ["ephys"],
            ["histology"],
            ["funcimg"],
            ["histology", "behav", "all_ses_level_non_data_type"],
        ],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_all_data_transfer_options(
        self,
        pathtable_and_project,
        sub_names,
        ses_names,
        data_type,
        upload_or_download,
    ):
        """
        Parse the arguments to filter the pathtable, getting
        the files expected to be transferred pased on the arguments
        Note files in sub/ses/datatype folders must be handled
        separately to those in non-sub, non-ses, non-data-type folders

        see test_utils.swap_local_and_remote_paths() for the logic
        on setting up and swapping local / remote paths for
        upload / download tests.
        """
        pathtable, project = pathtable_and_project

        transfer_function = test_utils.handle_upload_or_download(
            project, upload_or_download, swap_last_dir_only=project.testing_ssh
        )[0]

        transfer_function(sub_names, ses_names, data_type, init_log=False)

        if upload_or_download == "download":
            test_utils.swap_local_and_remote_paths(
                project, swap_last_dir_only=project.testing_ssh
            )

        sub_names = self.parse_arguments(pathtable, sub_names, "sub")
        ses_names = self.parse_arguments(pathtable, ses_names, "ses")
        data_type = self.parse_arguments(pathtable, data_type, "data_type")

        # Filter pathtable to get files that were expected
        # to be transferred
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

        # When transferring with SSH, there is a delay before
        # filesystem catches up
        if project.testing_ssh:
            time.sleep(10)

        # Check what paths were actually moved
        # (through the local filesystem), and test
        path_to_search = (
            self.remote_from_local(project.cfg["local_path"]) / "rawdata"
        )
        all_transferred = path_to_search.glob("**/*")
        paths_to_transferred_files = list(
            filter(Path.is_file, all_transferred)
        )

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

        # Teardown here, because we have session scope.
        try:
            shutil.rmtree(self.remote_from_local(project.cfg["local_path"]))
        except FileNotFoundError:
            pass

    # ---------------------------------------------------------------------------------------------------------------
    # Utils
    # ---------------------------------------------------------------------------------------------------------------

    def query_table(self, pathtable, arguments):
        """
        Search the table for arguments, return empty
        if arguments empty
        """
        if any(arguments):
            folders = pathtable.query(" | ".join(arguments))
        else:
            folders = pd.DataFrame()
        return folders

    def parse_arguments(self, pathtable, list_of_names, field):
        """
        Replicate datashuttle name formatting by parsing
        "all" arguments and turning them into a list of all names,
        (subject or session), taken from the pathtable.
        """
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
        """ """
        for i in range(pathtable.shape[0]):
            filepath = pathtable["base_dir"][i] / pathtable["path"][i]
            filepath.parents[0].mkdir(parents=True, exist_ok=True)
            test_utils.write_file(filepath, contents="test_entry")

    def make_pathtable_search_filter(self, sub_names, ses_names, data_type):
        """
        Create a string of arguments to pass to pd.query() that will
        create the table of only transferred sub, ses and data_type.

        Two arguments must be created, one of all sub / ses / datatypes
        and the other of all non sub/ non ses / non data type
        folders. These must be handled separately as they are
        mutually exclusive.
        """
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
