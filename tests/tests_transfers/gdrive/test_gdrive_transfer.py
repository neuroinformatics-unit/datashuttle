import pytest

from datashuttle.utils import rclone

from ..base_transfer import BaseTransfer
from . import gdrive_test_utils


class TestGdriveTransfer(BaseTransfer):
    @pytest.fixture(
        scope="class",
    )
    def gdrive_setup(self, pathtable_and_project):
        """
        Setup pathtable and project for GDrive transfer tests.
        """
        pathtable, project = pathtable_and_project

        gdrive_test_utils.setup_project_for_gdrive(
            project,
        )
        gdrive_test_utils.setup_gdrive_connection(project)

        project.upload_rawdata()

        yield [pathtable, project]

        rclone.call_rclone(
            f"purge central_{project.project_name}_gdrive:{project.cfg['central_path']}"
        )

    @pytest.mark.parametrize(
        "sub_names", [["all"], ["all_non_sub", "sub-002"]]
    )
    @pytest.mark.parametrize(
        "ses_names", [["all"], ["ses-002_random-key"], ["all_non_ses"]]
    )
    @pytest.mark.parametrize(
        "datatype", [["all"], ["anat", "all_non_datatype"]]
    )
    def test_combinations_gdrive_transfer(
        self,
        gdrive_setup,
        sub_names,
        ses_names,
        datatype,
    ):
        pathtable, project = gdrive_setup

        self.run_and_check_transfers(
            project, pathtable, sub_names, ses_names, datatype
        )
