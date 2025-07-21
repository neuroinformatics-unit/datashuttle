""" """

import fnmatch
import shutil
from pathlib import Path

import pytest

from ... import test_utils
from ..base_transfer import BaseTransfer

PARAM_SUBS = [
    ["all"],
    ["all_sub"],
    ["all_non_sub"],
    ["sub-001"],
    ["sub-003_date-20231201"],
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


class TestFileTransfer(BaseTransfer):
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
        Test many combinations of possible file transfer commands.
        """
        pathtable, project = pathtable_and_project

        paths_to_transferred_files = self.perform_transfer(
            project, upload_or_download, sub_names, ses_names, datatype
        )

        expected_transferred_paths = self.get_expected_transferred_paths(
            pathtable, sub_names, ses_names, datatype
        )

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

    # Test Wildcards
    # ----------------------------------------------------------------------------------
    # It is very difficult to test wildcards using the original machinery
    # for testing keywords such as "all", "all_sub" etc as used in test_combinations_filesystem_transfer().
    # Therefore, test a few specific cases here.

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_local_filesystem_wildcards_1(
        self, pathtable_and_project, upload_or_download
    ):
        """Test a single custom transfer that combines different special keywords."""
        pathtable, project = pathtable_and_project

        sub_names = ["@*@date@*@"]
        ses_names = ["all_ses"]
        datatype = ["funcimg"]

        paths_to_transferred_files = self.perform_transfer(
            project, upload_or_download, sub_names, ses_names, datatype
        )

        pathtable = pathtable[
            pathtable["parent_sub"]
            .fillna("")
            .apply(lambda x: fnmatch.fnmatch(x, "*date*"))
        ]

        pathtable = pathtable[
            pathtable["parent_datatype"].apply(lambda x: x == "funcimg")
        ]

        expected_transferred_paths = pathtable["path"]

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_local_filesystem_wildcards_2(
        self, pathtable_and_project, upload_or_download
    ):
        """Test a single custom transfer that combines different special keywords."""
        pathtable, project = pathtable_and_project

        sub_names = ["all_sub"]
        ses_names = ["ses-003@*@"]
        datatype = ["all_non_datatype"]

        paths_to_transferred_files = self.perform_transfer(
            project, upload_or_download, sub_names, ses_names, datatype
        )

        pathtable = pathtable[
            pathtable["parent_ses"]
            .fillna("")
            .apply(lambda x: fnmatch.fnmatch(x, "ses-003*"))
        ]

        pathtable = pathtable[
            pathtable["parent_datatype"].apply(lambda x: x is None)
        ]

        expected_transferred_paths = pathtable["path"]

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_local_filesystem_wildcards_3(
        self, pathtable_and_project, upload_or_download
    ):
        """Test a single custom transfer that combines different special keywords."""
        pathtable, project = pathtable_and_project

        sub_names = ["sub-002@TO@003_@*@"]
        ses_names = ["ses-001"]
        datatype = ["all"]

        paths_to_transferred_files = self.perform_transfer(
            project, upload_or_download, sub_names, ses_names, datatype
        )

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

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

    def perform_transfer(
        self, project, upload_or_download, sub_names, ses_names, datatype
    ):
        """Transfer the data, swapping the paths to move a subset of
        files from the already set up directory to a new directory
        using upload or download.

        The entire test project is created in the original `local_path`
        and subset of it is uploaded and tested against. To test
        upload vs. download, the `local_path` and `central_path`
        locations are swapped.
        """
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

        # Teardown here, because we have session scope.
        try:
            shutil.rmtree(self.central_from_local(project.cfg["local_path"]))
        except FileNotFoundError:
            pass

        return paths_to_transferred_files
