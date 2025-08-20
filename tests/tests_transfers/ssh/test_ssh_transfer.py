import fnmatch
import platform

import pytest

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
class TestSSHTransfer(BaseSSHTransfer):
    @pytest.fixture(
        scope="class",
    )
    def ssh_setup(self, pathtable_and_project, setup_ssh_container):
        """
        After initial project setup (in `pathtable_and_project`)
        setup a container and the project's SSH connection to the container.
        Then upload the test project to the `central_path`.
        """
        pathtable, project = pathtable_and_project

        ssh_test_utils.setup_project_for_ssh(
            project,
        )
        ssh_test_utils.setup_ssh_connection(project)

        project.upload_rawdata()

        return [pathtable, project]

    # -----------------------------------------------------------------
    # Test Setup SSH Connection
    # -----------------------------------------------------------------

    @pytest.mark.parametrize(
        "sub_names", [["all"], ["all_non_sub", "sub-002"]]
    )
    @pytest.mark.parametrize(
        "ses_names", [["all"], ["ses-002_random-key"], ["all_non_ses"]]
    )
    @pytest.mark.parametrize(
        "datatype", [["all"], ["anat", "all_non_datatype"]]
    )
    def test_combinations_ssh_transfer(
        self,
        ssh_setup,
        sub_names,
        ses_names,
        datatype,
    ):
        """
        Test a subset of argument combinations while testing over SSH connection
        to a container. This is very slow, due to the rclone ssh transfer (which
        is performed twice in this test, once for upload, once for download), around
        8 seconds per parameterization.
        """
        pathtable, project = ssh_setup

        expected_transferred_paths = self.get_expected_transferred_paths(
            pathtable, sub_names, ses_names, datatype
        )

        self.run_and_check_transfers(
            project, sub_names, ses_names, datatype, expected_transferred_paths
        )

    # Test Wildcards
    # ----------------------------------------------------------------------------------
    # It is very difficult to test wildcards using the original machinery
    # for testing keywords such as "all", "all_sub" etc as used in test_combinations_ssh_transfer().
    # Therefore, test a few specific cases here by manually chopping down the pathtable based
    # on the sub / ses /datatype names to test the expected paths.

    def test_ssh_wildcards_1(self, ssh_setup):
        """Test a single custom transfer that combines different special keywords."""
        pathtable, project = ssh_setup

        sub_names = ["@*@date@*@"]
        ses_names = ["all_ses"]
        datatype = ["funcimg"]

        pathtable = pathtable[
            pathtable["parent_sub"]
            .fillna("")
            .apply(lambda x: fnmatch.fnmatch(x, "*date*"))
        ]

        pathtable = pathtable[
            pathtable["parent_datatype"].apply(lambda x: x == "funcimg")
        ]

        expected_transferred_paths = pathtable["path"]

        self.run_and_check_transfers(
            project, sub_names, ses_names, datatype, expected_transferred_paths
        )

    def test_ssh_wildcards_2(self, ssh_setup):
        """Test a single custom transfer that combines different special keywords."""
        pathtable, project = ssh_setup

        sub_names = ["all_sub"]
        ses_names = ["ses-003@*@"]
        datatype = ["all_non_datatype"]

        pathtable = pathtable[
            pathtable["parent_ses"]
            .fillna("")
            .apply(lambda x: fnmatch.fnmatch(x, "ses-003*"))
        ]

        pathtable = pathtable[
            pathtable["parent_datatype"].apply(lambda x: x is None)
        ]

        expected_transferred_paths = pathtable["path"]

        self.run_and_check_transfers(
            project, sub_names, ses_names, datatype, expected_transferred_paths
        )

    def test_ssh_wildcards_3(self, ssh_setup):
        """Test a single custom transfer that combines different special keywords."""
        pathtable, project = ssh_setup

        sub_names = ["sub-002@TO@003_@*@"]
        ses_names = ["ses-001"]
        datatype = ["all"]

        pathtable = pathtable[
            pathtable["parent_sub"]
            .fillna("")
            .apply(
                lambda x: fnmatch.fnmatch(x, "sub-002*")
                or fnmatch.fnmatch(x, "sub-003*")
            )
        ]

        pathtable = pathtable[
            pathtable["parent_ses"]
            .fillna("")
            .apply(lambda x: fnmatch.fnmatch(x, "ses-001"))
        ]

        expected_transferred_paths = pathtable["path"]

        self.run_and_check_transfers(
            project, sub_names, ses_names, datatype, expected_transferred_paths
        )
