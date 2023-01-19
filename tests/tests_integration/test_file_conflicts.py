"""
# Still need to do more of this.
# 4) test all, in particular the removal of --ignore-existing. When the user transfers, it makes
#    sense to have a comment explicitly stating the nature of the transfer (or, at the end).

"""
import os
from pathlib import Path

import pytest
import test_utils


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

    def write_file(self, path_, message, append=False):
        key = "a" if append else "w"
        with open(path_, key) as file:
            file.write(message)

    def read_file(self, path_):
        with open(path_, "r") as file:
            contents = file.readlines()
        return contents

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
        self.write_file(local_test_file_path, "first edit")

        time_written = os.path.getatime(local_test_file_path)

        if overwrite_old_files_on_transfer:
            project.update_config("overwrite_old_files_on_transfer", True)

        project.upload_all()

        # Update the file and transfer and transfer again
        self.write_file(local_test_file_path, " second edit", append=True)

        assert time_written < os.path.getatime(local_test_file_path)

        project.upload_all()

        remote_contents = self.read_file(remote_test_file_path)

        if overwrite_old_files_on_transfer:
            assert remote_contents == ["first edit second edit"]
        else:
            assert remote_contents == ["first edit"]


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

# def test_all_data_transfer_options()


# https://stackoverflow.com/questions/18601828/python-block-network-connections-for-testing-purposes
# but these drop python access to internet NOT entire internet (at least some of them)

# PROJECT / SUB / SES LEVEL UNTRACKED FILES
# add keyword arguments a la #70

# Note: Use the -P/--progress flag to view real-time transfer statistics.

# new rclone args:
#   --progress
#   ignore-existing
#   verbosity
