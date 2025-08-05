import pytest

from datashuttle.utils import rclone

from ..base_transfer import BaseTransfer
from . import aws_test_utils


class TestAwsTransfer(BaseTransfer):
    @pytest.fixture(
        scope="class",
    )
    def aws_setup(self, pathtable_and_project):
        """
        Setup pathtable and project for AWS transfer tests.
        """
        pathtable, project = pathtable_and_project

        aws_test_utils.setup_project_for_aws(project)
        aws_test_utils.setup_aws_connection(project)

        project.upload_rawdata()

        yield [pathtable, project]

        rclone.call_rclone(
            f"purge central_{project.project_name}_aws:{project.cfg['central_path']}"
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
    def test_combinations_aws_transfer(
        self,
        aws_setup,
        sub_names,
        ses_names,
        datatype,
    ):
        pathtable, project = aws_setup

        self.run_and_check_transfers(
            project, pathtable, sub_names, ses_names, datatype
        )
