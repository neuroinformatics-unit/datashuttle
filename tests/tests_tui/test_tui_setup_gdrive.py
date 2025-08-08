import os

import pytest

from datashuttle.tui.app import TuiApp

from .. import test_utils
from .tui_base import TuiBase


class TestTuiSetupGdrive(TuiBase):
    @pytest.mark.asyncio
    async def test_gdrive_connection_setup_without_browser(
        self, setup_project_paths
    ):
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
                ).renderable
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
                ).renderable
            )

    @pytest.mark.asyncio
    async def test_gdrive_connection_setup_incorrect_config_token(
        self, setup_project_paths
    ):
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
                ).renderable
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
                ).renderable
            )

    @pytest.mark.asyncio
    async def test_gdrive_connection_setup_incorrect_root_folder_id(
        self, setup_project_paths
    ):
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
                ).renderable
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
                ).renderable
            )
            assert (
                "Error 404: File not found"
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                ).renderable
            )

    @pytest.mark.asyncio
    async def test_cancel_gdrive_connection_setup(self, setup_project_paths):
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
                "Please authenticate through browser."
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                ).renderable
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_cancel_button"
            )

            # Try setting up the connection again
            await self.setup_gdrive_connection_via_tui(pilot)
            assert (
                "Please authenticate through browser."
                in pilot.app.screen.query_one(
                    "#gdrive_setup_messagebox_message"
                ).renderable
            )
            await self.scroll_to_click_pause(
                pilot, "#setup_gdrive_cancel_button"
            )

    async def setup_gdrive_project(
        self, pilot, project_name, gdrive_client_id, root_folder_id
    ):
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

        await self.scroll_to_click_pause(pilot, "#configs_save_configs_button")
        await self.close_messagebox(pilot)

    async def setup_gdrive_connection_via_tui(
        self, pilot, with_browser: bool = True
    ):
        await self.scroll_to_click_pause(
            pilot, "#configs_setup_connection_button"
        )

        assert (
            "Ready to setup Google Drive. Press OK to proceed"
            in pilot.app.screen.query_one(
                "#gdrive_setup_messagebox_message"
            ).renderable
        )
        await self.scroll_to_click_pause(pilot, "#setup_gdrive_ok_button")

        assert (
            "Please provide the client secret for Google Drive. "
            "You can find it in your Google Cloud Console."
            in pilot.app.screen.query_one(
                "#gdrive_setup_messagebox_message"
            ).renderable
        )
        await self.fill_input(
            pilot,
            "#setup_gdrive_generic_input_box",
            os.environ["GDRIVE_CLIENT_SECRET"],
        )
        await self.scroll_to_click_pause(pilot, "#setup_gdrive_enter_button")

        assert (
            "Are you running Datashuttle on a machine "
            "that can open a web browser?"
            in pilot.app.screen.query_one(
                "#gdrive_setup_messagebox_message"
            ).renderable
        )

        if with_browser:
            await self.scroll_to_click_pause(pilot, "#setup_gdrive_yes_button")
        else:
            await self.scroll_to_click_pause(pilot, "#setup_gdrive_no_button")
