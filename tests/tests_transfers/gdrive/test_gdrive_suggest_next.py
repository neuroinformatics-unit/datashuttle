import shutil

import pytest

from datashuttle.utils import rclone

from ... import test_utils
from ...tests_tui.tui_base import TuiBase
from ..base_transfer import BaseTransfer
from . import gdrive_test_utils


@pytest.mark.skipif(
    not gdrive_test_utils.has_gdrive_environment_variables(),
    reason="Google Drive set up environment variables must be set.",
)
class TestGDriveSuggestNext(BaseTransfer, TuiBase):
    @pytest.fixture(
        scope="function",
    )
    def gdrive_setup(self, setup_project_paths):
        """
        Setup pathtable and project for GDrive transfer tests.
        """
        project = test_utils.make_project(setup_project_paths["project_name"])
        gdrive_test_utils.setup_project_for_gdrive(
            project,
        )
        gdrive_test_utils.setup_gdrive_connection(project)

        yield project

        rclone.call_rclone(
            f"purge central_{project.project_name}_gdrive:{project.cfg['central_path'].parent}"
        )

    @pytest.mark.asyncio
    async def test_gdrive_suggest_next_sub_ses(
        self,
        gdrive_setup,
    ):
        """ """
        project = gdrive_setup

        test_utils.make_local_folders_with_files_in(
            project, "rawdata", "sub-001", ["ses-001", "ses-002"]
        )
        project.upload_entire_project()

        shutil.rmtree(project.get_local_path())

        await self.check_next_sub_002_ses_003_in_tui(project)
