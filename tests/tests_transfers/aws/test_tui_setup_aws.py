import os

import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.project_manager import ProjectManagerScreen
from datashuttle.utils import rclone, utils

from ...tests_tui.tui_base import TuiBase
from . import aws_test_utils


@pytest.mark.skipif(
    not aws_test_utils.has_aws_environment_variables(),
    reason="AWS set up environment variables must be set.",
)
class TestTuiSetupAws(TuiBase):
    """
    Set up the connection to AWS via the TUI. These tests require
    environment variables to be set to allow the full set up,
    like other transfer tests.
    """

    @pytest.fixture(scope="function")
    def central_path_and_project(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        aws_bucket_name = os.environ["AWS_BUCKET_NAME"]
        random_prefix = utils.get_random_string()
        central_path = f"{aws_bucket_name}/{random_prefix}"

        yield central_path, project_name

        rclone.call_rclone(f"purge central_{project_name}_aws:{central_path}")

    @pytest.mark.asyncio
    async def test_aws_connection_setup(self, central_path_and_project):
        """Test AWS connection setup via the TUI.

        AWS connection details are filled in the configs tab. The setup
        process is run and final connection success output is checked.
        The credentials in the environment are set by the CI. For testing
        locally, the developer must set these themselves.
        """
        central_path, project_name = central_path_and_project

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.setup_aws_project_and_run_connection_setup(
                pilot,
                central_path=central_path,
                secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            )

            assert (
                "AWS Connection Successful!"
                in pilot.app.screen.query_one("#setup_aws_messagebox_message")
                .render()
                .plain
            )

    @pytest.mark.asyncio
    async def test_aws_connection_setup_failed(self, central_path_and_project):
        """Test AWS connection setup using an incorrect client secret and check
        for a failed message on the output.
        """
        central_path, project_name = central_path_and_project

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.setup_aws_project_and_run_connection_setup(
                pilot,
                central_path=central_path,
                secret_access_key="some-random-client-secret",
            )

            assert (
                "AWS setup failed. Please check your configs and secret access key"
                in pilot.app.screen.query_one("#setup_aws_messagebox_message")
                .render()
                .plain
            )

    async def setup_aws_project_and_run_connection_setup(
        self, pilot, central_path, secret_access_key
    ):
        """Set up AWS project via the configs tab and run the connection setup."""
        await self.setup_aws_project(pilot, central_path)

        await self.scroll_to_click_pause(
            pilot, "#configs_setup_connection_button"
        )

        # Start connection setup
        assert (
            "Ready to setup AWS connection. Press OK to proceed"
            in pilot.app.screen.query_one("#setup_aws_messagebox_message")
            .render()
            .plain
        )
        await self.scroll_to_click_pause(pilot, "#setup_aws_ok_button")

        # Fill secret access key
        assert (
            "Please Enter your AWS Secret Access Key"
            in pilot.app.screen.query_one("#setup_aws_messagebox_message")
            .render()
            .plain
        )
        await self.fill_input(
            pilot,
            "#setup_aws_secret_access_key_input",
            secret_access_key,
        )

        await self.scroll_to_click_pause(pilot, "#setup_aws_ok_button")

    async def setup_aws_project(self, pilot, central_path):
        """Navigate to the configs tab, fill in the AWS config credentials and save them."""
        assert isinstance(pilot.app.screen, ProjectManagerScreen)

        await self.switch_tab(pilot, "configs")
        await self.scroll_to_click_pause(pilot, "#configs_aws_radiobutton")

        # Fill connection details
        await self.fill_input(
            pilot,
            "#configs_aws_access_key_id_input",
            os.environ["AWS_ACCESS_KEY_ID"],
        )

        select = pilot.app.screen.query_one("#configs_aws_region_select")
        select.value = os.environ["AWS_REGION"]

        await self.fill_input(
            pilot, "#configs_central_path_input", central_path
        )

        await self.scroll_to_click_pause(pilot, "#configs_save_configs_button")
        await self.close_messagebox(pilot)
