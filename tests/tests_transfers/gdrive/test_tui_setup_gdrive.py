import os

import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.project_manager import ProjectManagerScreen
from datashuttle.utils import rclone, utils

from ... import test_utils
from ...tests_tui.tui_base import TuiBase
from . import gdrive_test_utils


@pytest.mark.skipif(
    not gdrive_test_utils.has_gdrive_environment_variables(),
    reason="Google Drive set up environment variables must be set.",
)
class TestTuiSetupGdrive(TuiBase):
    """
    Set up the connection to GDrive via the TUI. These tests require
    environment variables to be set to allow the full set up,
    like other transfer tests.
    """

    @pytest.fixture(scope="function")
    def central_path_and_project(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        random_prefix = utils.get_random_string()
        central_path = f"/{random_prefix}"

        yield central_path, project_name

        rclone.call_rclone(
            f"purge central_{project_name}_gdrive:{central_path}"
        )

    @pytest.mark.parametrize("central_path_none", [True, False])
    @pytest.mark.asyncio
    async def test_gdrive_connection_setup_without_browser(
        self, central_path_none, central_path_and_project
    ):
        """Test Google Drive connection setup via the TUI.

        Google Drive connection details are filled in the configs tab. The setup
        process is run and final connection success output is checked. Since it's
        not possible to authenticate via a browser during tests, the connection
        setup is tested without a browser. The credentials in the environment are
        set by the CI. For testing locally, the developer must set these themselves.
        """
        central_path, project_name = central_path_and_project

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.setup_gdrive_project(
                pilot,
                project_name,
                os.environ["GDRIVE_CLIENT_ID"],
                os.environ["GDRIVE_ROOT_FOLDER_ID"],
                central_path=central_path if not central_path_none else "",
            )

            await self.setup_gdrive_connection_via_tui(
                pilot, with_browser=False
            )

            assert (
                "Press shift+click to copy."
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )

            # Fill the config token
            await self.fill_input(
                pilot,
                "#setup_gdrive_generic_input_box",
                os.environ["GDRIVE_CONFIG_TOKEN"],
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_enter_button"
            )

            await test_utils.await_task_by_name_if_present(
                "setup_gdrive_connection_without_browser_task"
            )

            assert (
                "Setup Complete!"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )

    @pytest.mark.asyncio
    async def test_gdrive_connection_setup_incorrect_config_token(
        self, setup_project_paths
    ):
        """Test Google Drive connection setup using an incorrect config token and check
        for a failed message on the output.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.setup_gdrive_project(
                pilot,
                project_name,
                os.environ["GDRIVE_CLIENT_ID"],
                os.environ["GDRIVE_ROOT_FOLDER_ID"],
            )

            await self.setup_gdrive_connection_via_tui(
                pilot, with_browser=False
            )

            assert (
                "Press shift+click to copy."
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )

            # Fill the config token
            await self.fill_input(
                pilot,
                "#setup_gdrive_generic_input_box",
                "placeholder",
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_enter_button"
            )

            await test_utils.await_task_by_name_if_present(
                "setup_gdrive_connection_without_browser_task"
            )

            assert (
                "Google Drive setup failed. Please check your credentials"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )

            await self.scroll_to_click_pause(pilot, "#setup_gdrive_ok_button")

            assert (
                pilot.app.screen.query_one(
                    "#configs_go_to_project_screen_button"
                ).visible
                is True
            )

    @pytest.mark.asyncio
    async def test_gdrive_connection_setup_incorrect_root_folder_id(
        self, setup_project_paths
    ):
        """Test Google Drive connection setup using an incorrect root folder ID
        and check for a failed message on the output.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.setup_gdrive_project(
                pilot,
                project_name,
                os.environ["GDRIVE_CLIENT_ID"],
                "placeholder",
            )

            await self.setup_gdrive_connection_via_tui(
                pilot, with_browser=False
            )

            assert (
                "Press shift+click to copy."
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )

            # Fill the config token
            await self.fill_input(
                pilot,
                "#setup_gdrive_generic_input_box",
                os.environ["GDRIVE_CONFIG_TOKEN"],
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_enter_button"
            )

            await test_utils.await_task_by_name_if_present(
                "setup_gdrive_connection_without_browser_task"
            )

            assert (
                "Google Drive setup failed. Please check your credentials"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )
            assert (
                "Error 404: File not found"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )

    @pytest.mark.asyncio
    async def test_cancel_gdrive_connection_setup(self, setup_project_paths):
        """Test cancelling the Google Drive setup and then try to rerun the setup.

        After having run a Google Drive setup, to run a Google Drive setup again, it
        is mandatory to stop/exit the old setup process so as to free the port used by
        rclone for running Google's oauth locally. This was done by using `subprocess.Popen`
        and killing the process once the cancel button is pressed. This is being tested here
        to ensure that the Google Drive setup can be rerun after being cancelled.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()

        async with app.run_test(size=self.tui_size()) as pilot:
            await self.setup_gdrive_project(
                pilot,
                project_name,
                os.environ["GDRIVE_CLIENT_ID"],
                os.environ["GDRIVE_ROOT_FOLDER_ID"],
            )

            # Setup connection and cancel midway
            await self.setup_gdrive_connection_via_tui(pilot)
            assert (
                "Please authenticate through browser"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_cancel_button"
            )

            # Try setting up the connection again
            await self.setup_gdrive_connection_via_tui(pilot)
            assert (
                "Please authenticate through browser"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                )
                .render()
                .plain
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_cancel_button"
            )

            assert isinstance(pilot.app.screen, ProjectManagerScreen)

    async def setup_gdrive_project(
        self,
        pilot,
        project_name,
        gdrive_client_id,
        root_folder_id,
        central_path: str = "",
    ):
        """Navigate to the configs tab, fill in the Google Drive config credentials and save them."""

        await self.check_and_click_onto_existing_project(pilot, project_name)
        await self.switch_tab(pilot, "configs")
        await self.scroll_to_click_pause(pilot, "#configs_gdrive_radiobutton")

        # Fill connection details
        await self.fill_input(
            pilot, "#configs_gdrive_client_id_input", gdrive_client_id
        )
        await self.fill_input(
            pilot, "#configs_gdrive_root_folder_id_input", root_folder_id
        )

        await self.fill_input(
            pilot, "#configs_central_path_input", central_path
        )

        await self.scroll_to_click_pause(pilot, "#configs_save_configs_button")
        await self.close_messagebox(pilot)

    async def setup_gdrive_connection_via_tui(
        self, pilot, with_browser: bool = True
    ):
        """This is a utility function that starts the Google Drive connection setup, fills
        in the Google Drive client secret and answers a yes/no for the browser present question.

        Further process of the setup is done by the respective tests.
        """
        await self.scroll_to_click_pause(
            pilot, "#configs_setup_connection_button"
        )

        assert (
            "Ready to setup Google Drive. Press OK to proceed"
            in pilot.app.screen.query_one("#gdrive_setup_messagebox_message")
            .render()
            .plain
        )
        await self.scroll_to_click_pause(pilot, "#setup_gdrive_ok_button")

        assert (
            "Please provide the client secret for Google Drive. "
            "You can find it in your Google Cloud Console."
            in pilot.app.screen.query_one("#gdrive_setup_messagebox_message")
            .render()
            .plain
        )
        await self.fill_input(
            pilot,
            "#setup_gdrive_generic_input_box",
            os.environ["GDRIVE_CLIENT_SECRET"],
        )
        await self.scroll_to_click_pause(pilot, "#setup_gdrive_enter_button")

        assert (
            "Are you running datashuttle on a machine "
            "that can open a web browser?"
            in pilot.app.screen.query_one("#gdrive_setup_messagebox_message")
            .render()
            .plain
        )

        if with_browser:
            await self.scroll_to_click_pause(pilot, "#setup_gdrive_yes_button")
        else:
            await self.scroll_to_click_pause(pilot, "#setup_gdrive_no_button")
