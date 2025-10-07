import platform

import pytest

from ... import test_utils
from ...tests_tui.tui_base import TuiBase
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
class TestSSHDriveSuggestNext(BaseSSHTransfer, TuiBase):
    @pytest.fixture(
        scope="function",
    )
    def ssh_setup(self, setup_project_paths, setup_ssh_container_fixture):
        """
        Setup pathtable and project for GDrive transfer tests.
        """
        project = test_utils.make_project(setup_project_paths["project_name"])
        ssh_test_utils.setup_project_for_ssh(
            project,
        )
        ssh_test_utils.setup_ssh_connection(project)

        yield project

    @pytest.mark.asyncio
    async def test_ssh_suggest_next_sub_ses(
        self,
        ssh_setup,
    ):
        """ """
        project = ssh_setup

        await self.check_next_sub_ses_in_tui(project)
