"""
# Still need to do more of this.
# 4) test all, in particular the removal of --ignore-existing. When the user transfers, it makes
#    sense to have a comment explicitly stating the nature of the transfer (or, at the end).

# https://stackoverflow.com/questions/18601828/python-block-network-connections-for-testing-purposes
# but these drop python access to internet NOT entire internet (at least some of them)

# PROJECT / SUB / SES LEVEL UNTRACKED FILES
# add keyword arguments a la #70

# Note: Use the -P/--progress flag to view real-time transfer statistics.

# new rclone args:
#   --progress
#   ignore-existing
#   verbosity

# dont forget to type everything!

# possible inputs
# ---------------

# sub_names: "all", "all_sub", "all_non_sub", [some sub names]

# ses_names: "all", "all_ses", "all_non_ses", [some ses_names]

# data_type: "all", "all_data_type", "all_ses_level_non_data_type", [some data type names]

# path table
# ---------------

# Path : full path to file
# is_dir : True if directory, False if file
# level : "project", "sub" or "ses" (i.e. it is in the top level folder (e.g. rawdata), subject levle, or session level.
# parent_sub : if ses file or other, name of the parent subject (otherwise None)
# parent_ses : if data type or other file, name of the parent session folder
# is_data_type : the data type if True, otherwise None

# DONT FORGET THIS IS SUPPOSE TO TEST OVER SSH
# ASK ALEX ABOUT SSH TO CEPH

# fmt: off

# this would work for data_type and all other files. But didn't work well for testing, so just use the files.
# TODO: fix naming

# how to handle this, because this should be tested as a normal file transfer without SSH. Maybe call these extended
# tests, and test with SSH only if set!

# manualyl check this test is doing what I think it is and check all edge cases
"""

import os
from pathlib import Path

import pandas as pd
import pytest
import test_utils
from test_file_conflicts_pathtable import get_pathtable


class TestFileTransfer:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """
        Create a project with default configs loaded.
        This makes a fresh project for each function,
        saved in the appdir path for platform independent
        and to avoid path setup on new machine.

        Ensure change dir at end of session otherwise it
        is not possible to delete project.
        """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_file_conflicts"
        project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )

        yield project
        test_utils.teardown_project(cwd, project)

    # ---------------------------------------------------------------------------------------------------------------
    # Test Rclone File Overwrite
    # ---------------------------------------------------------------------------------------------------------------

    @pytest.mark.skip
    @pytest.mark.parametrize("overwrite_old_files_on_transfer", [True, False])
    def test_rclone_overwrite_modified_file(
        self, project, overwrite_old_files_on_transfer
    ):
        """
        Test how rclone deals with existing files. In datashuttle
        if project.cfg["overwrite_old_files_on_transfer"] is on,
        files will be replaced with newer versions. Alternatively,
        if this is off, files will never be overwritten even if
        the version in source is newer than target.
        """
        path_to_test_file = (
            Path("rawdata") / "sub-001" / "histology" / "test_file.txt"
        )

        project.make_sub_dir("sub-001")
        local_test_file_path = project.cfg["local_path"] / path_to_test_file
        remote_test_file_path = project.cfg["remote_path"] / path_to_test_file

        # Write a local file and transfer
        self.write_file(local_test_file_path, contents="first edit")

        time_written = os.path.getatime(local_test_file_path)

        if overwrite_old_files_on_transfer:
            project.update_config("overwrite_old_files_on_transfer", True)

        project.upload_all()

        # Update the file and transfer and transfer again
        self.write_file(
            local_test_file_path, contents=" second edit", append=True
        )

        assert time_written < os.path.getatime(local_test_file_path)

        project.upload_all()

        remote_contents = self.read_file(remote_test_file_path)

        if overwrite_old_files_on_transfer:
            assert remote_contents == ["first edit second edit"]
        else:
            assert remote_contents == ["first edit"]

    # ---------------------------------------------------------------------------------------------------------------
    # Test File Transfer - All Options
    # ---------------------------------------------------------------------------------------------------------------

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
        "ses_names", [["all"], ["all_ses"], ["all_non_ses"], ["ses_002"]]
    )
    @pytest.mark.parametrize(
        "data_type",
        [
            ["all"],
            ["all_ses_level_non_data_type"],
            ["behav"],
            ["ephys"],
            ["histology"],
            ["funcimg"],
            ["histology", "behav", "all_ses_level_non_data_type"],
        ],
    )
    def test_all_data_transfer_options(
        self, project, sub_names, ses_names, data_type
    ):
        """ """
        pathtable = get_pathtable(project.cfg["local_path"])

        # Make and transfer all files in the pathtable,
        # then upload a subset according to the passed arguments
        self.create_all_pathtable_files(pathtable)

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
        all_transferred = project.cfg["remote_path"].glob("**/*")
        paths_to_transferred_files = filter(Path.is_file, all_transferred)

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

    # ---------------------------------------------------------------------------------------------------------------
    # Utils
    # ---------------------------------------------------------------------------------------------------------------

    def write_file(self, path_, contents, append=False):
        key = "a" if append else "w"
        with open(path_, key) as file:
            file.write(contents)

    def read_file(self, path_):
        with open(path_, "r") as file:
            contents = file.readlines()
        return contents

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
            self.write_file(filepath, contents="test_entry")

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
