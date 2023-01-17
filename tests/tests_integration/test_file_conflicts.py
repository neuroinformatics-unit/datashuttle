import os

import pytest
import test_utils


@pytest.mark.skip(reason="IN PROGRESS")
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

    def test_rclone_overwrite_modified_file(self, project):
        """"""
        project.make_sub_dir("sub-001")
        local_test_file_path = (
            project.cfg["local_path"]
            / "rawdata"
            / "sub-001"
            / "histology"
            / "test_file.txt"
        )
        remote_test_file_path = (
            project.cfg["remote_path"]
            / "rawdata"
            / "sub-001"
            / "histology"
            / "test_file.txt"
        )

        # Write a local file and transfer
        self.write_file(local_test_file_path, "first edit")

        time_written = os.path.getatime(local_test_file_path)

        project.upload_all()

        # Update the file and transfer, the remote file should not be
        # ovewritten.

        self.write_file(local_test_file_path, "second edit", append=True)

        assert time_written < os.path.getatime(local_test_file_path)

        project.upload_all()

        remote_contents = self.read_file(remote_test_file_path)

        assert remote_contents == ["first edit"]


# NEW ARGS
# 1) add all new rclone flags (decide if own dict or kwargs, kwargs probably better) to API
# 2) add all new flags to CLI
# 3) Add to docstrings, and check. Doc in the documentation

# 4) test all, in particular the removal of --ignore-existing. When the user transfers, it makes
#    sense to have a comment explicitly stating the nature of the transfer (or, at the end).


# PROJECT / SUB / SES LEVEL UNTRACKED FILES
# add keyword arguments a la #70

# Note: Use the -P/--progress flag to view real-time transfer statistics.

# new rclone args:
#   --progress
#   ignore-existing
#   verbosity
