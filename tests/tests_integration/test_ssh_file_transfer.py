""" """

import shutil
from pathlib import Path

import pytest
import ssh_test_utils
import test_utils
from base_transfer import BaseTransfer

TEST_SSH = ssh_test_utils.get_test_ssh()

PARAM_SUBS = [
    ["all"],
    ["all_sub"],
    ["all_non_sub"],
    ["sub-001"],
    ["sub-003_date-20231901"],
    ["sub-002", "all_non_sub"],
]
PARAM_SES = [
    ["all"],
    ["all_non_ses"],
    ["all_ses"],
    ["ses-001"],
    ["ses-002_random-key"],
    ["all_non_ses", "ses-001"],
]
PARAM_DATATYPE = [
    ["all"],
    ["all_non_datatype"],
    ["all_datatype"],
    ["behav"],
    ["ephys"],
    ["anat"],
    ["funcimg"],
    ["anat", "behav", "all_non_datatype"],
]

class TestFileTransfer:
    @pytest.fixture(
        scope="class",
    )
    def pathtable_and_project(self, tmpdir_factory):
        """
        Create a new test project with a test project folder
        and file structure (see `get_pathtable()` for definition).
        """
        tmp_path = tmpdir_factory.mktemp("test")

        base_path = tmp_path / "test with space"
        test_project_name = "test_file_conflicts"

        project = test_utils.setup_project_fixture(
            base_path, test_project_name
        )

        if testing_ssh:
            ssh_test_utils.setup_project_for_ssh(
                project,
                test_utils.make_test_path(
                    central_path, "central", test_project_name
                ),
                ssh_config.CENTRAL_HOST_ID,
                ssh_config.USERNAME,
            )

            # Initialise the SSH connection
            ssh_test_utils.build_docker_image(project)

            ssh_test_utils.setup_hostkeys(project)

        pathtable = get_pathtable(project.cfg["local_path"])

        self.create_all_pathtable_files(pathtable)

        yield [pathtable, project]

        test_utils.teardown_project(project)

    @pytest.fixture(
        scope="class",
    )
    def ssh_setup(self, pathtable_and_project):
        """
        After initial project setup (in `pathtable_and_project`)
        setup a container and the project's SSH connection to the container.
        Then upload the test project to the `central_path`.
        """
        pathtable, project = pathtable_and_project
        ssh_test_utils.setup_project_and_container_for_ssh(project)
        ssh_test_utils.setup_ssh_connection(project)

        project.upload_rawdata()

        return [pathtable, project]

    # ----------------------------------------------------------------------------------
    # Test File Transfer - All Options
    # ----------------------------------------------------------------------------------

    @pytest.mark.parametrize("sub_names", PARAM_SUBS)
    @pytest.mark.parametrize("ses_names", PARAM_SES)
    @pytest.mark.parametrize("datatype", PARAM_DATATYPE)
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_combinations_filesystem_transfer(
        self,
        pathtable_and_project,
        sub_names,
        ses_names,
        datatype,
        upload_or_download,
    ):
        """
        Test many combinations of possible file transfer commands. The
        entire test project is created in the original `local_path`
        and subset of it is uploaded and tested against. To test
        upload vs. download, the `local_path` and `central_path`
        locations are swapped.
        """
        pathtable, project = pathtable_and_project

        # Transfer the data, swapping the paths to move a subset of
        # files from the already set up directory to a new directory
        # using upload or download.
        transfer_function = test_utils.handle_upload_or_download(
            project,
            upload_or_download,
            transfer_method="custom",
            swap_last_folder_only=False,
        )[0]

        transfer_function(
            "rawdata", sub_names, ses_names, datatype, init_log=False
        )

        if upload_or_download == "download":
            test_utils.swap_local_and_central_paths(
                project, swap_last_folder_only=False
            )

        expected_transferred_paths = self.get_expected_transferred_paths(
            pathtable, sub_names, ses_names, datatype
        )

        # Check what paths were actually moved
        # (through the local filesystem), and test
        path_to_search = (
            self.central_from_local(project.cfg["local_path"]) / "rawdata"
        )
        all_transferred = path_to_search.glob("**/*")

        paths_to_transferred_files = list(
            filter(Path.is_file, all_transferred)
        )

        paths_to_transferred_files = self.remove_path_before_rawdata(
            paths_to_transferred_files
        )

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

        # Teardown here, because we have session scope.
        try:
            shutil.rmtree(self.central_from_local(project.cfg["local_path"]))
        except FileNotFoundError:
            pass
