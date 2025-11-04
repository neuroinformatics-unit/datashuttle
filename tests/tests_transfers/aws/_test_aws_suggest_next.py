import pytest

from datashuttle.utils import rclone

from ... import test_utils
from ...tests_tui.tui_base import TuiBase
from ..base_transfer import BaseTransfer
from . import aws_test_utils


@pytest.mark.skipif(
    not aws_test_utils.has_aws_environment_variables(),
    reason="AWS set up environment variables must be set.",
)
class TestAWSSuggestNext(BaseTransfer, TuiBase):
    @pytest.fixture(
        scope="function",
    )
    def aws_setup(self, setup_project_paths):
        """
        Setup pathtable and project for AWS transfer tests.
        """
        project = test_utils.make_project(setup_project_paths["project_name"])
        aws_test_utils.setup_project_for_aws(project)
        aws_test_utils.setup_aws_connection(project)

        yield project

        rclone.call_rclone(
            f"purge central_{project.project_name}_gdrive:{project.cfg['central_path'].parent} {rclone.get_config_arg(project.cfg)}"
        )

    @pytest.mark.asyncio
    async def test_aws_suggest_next_sub_ses(
        self,
        aws_setup,
    ):
        """ """
        project = aws_setup

        await self.check_next_sub_ses_in_tui(project)
