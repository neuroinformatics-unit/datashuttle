import os

import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.project_manager import ProjectManagerScreen

from .tui_base import TuiBase


class TestTuiSetupAws(TuiBase):
    @pytest.mark.asyncio
    async def test_aws_connection_setup(self, setup_project_paths):
        """Test AWS connection setup via the TUI.

        AWS connection details are filled in the configs tab. The setup
        process is run and final connection success output is checked.
        The credentials in the environment are set by the CI. For testing
        locally, the developer must set these themselves.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.setup_aws_project_and_run_connection_setup(
                pilot, os.environ["AWS_SECRET_ACCESS_KEY"]
            )

            assert (
                "AWS Connection Successful!"
                in pilot.app.screen.query_one(
                    "#setup_aws_messagebox_message"
                ).renderable
            )

    @pytest.mark.asyncio
    async def test_aws_connection_setup_failed(self, setup_project_paths):
        """Test AWS connection setup using an incorrect client secret and check
        for a failed message on the output.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.setup_aws_project_and_run_connection_setup(
                pilot, "some-random-client-secret"
            )

            assert (
                "AWS setup failed. Please check your configs and secret access key"
                in pilot.app.screen.query_one(
                    "#setup_aws_messagebox_message"
                ).renderable
            )

    async def setup_aws_project_and_run_connection_setup(
        self, pilot, secret_access_key
    ):
        """Set up AWS project via the configs tab and run the connection setup."""
        await self.setup_aws_project(pilot)

        await self.scroll_to_click_pause(
            pilot, "#configs_setup_connection_button"
        )

        # Start connection setup
        assert (
            "Ready to setup AWS connection. Press OK to proceed"
            in pilot.app.screen.query_one(
                "#setup_aws_messagebox_message"
            ).renderable
        )
        await self.scroll_to_click_pause(pilot, "#setup_aws_ok_button")

        # Fill secret access key
        assert (
            "Please Enter your AWS Secret Access Key"
            in pilot.app.screen.query_one(
                "#setup_aws_messagebox_message"
            ).renderable
        )
        await self.fill_input(
            pilot,
            "#setup_aws_secret_access_key_input",
            secret_access_key,
        )

        await self.scroll_to_click_pause(pilot, "#setup_aws_ok_button")

    async def setup_aws_project(self, pilot):
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

        aws_bucket_name = os.environ["AWS_BUCKET_NAME"]
        await self.fill_input(
            pilot, "#configs_central_path_input", f"{aws_bucket_name}/main"
        )

        await self.scroll_to_click_pause(pilot, "#configs_save_configs_button")
        await self.close_messagebox(pilot)
