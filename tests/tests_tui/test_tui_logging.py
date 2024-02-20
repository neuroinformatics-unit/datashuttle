import pytest
from tui_base import TuiBase

from datashuttle import DataShuttle
from datashuttle.tui.app import TuiApp
from datashuttle.tui.tabs.logging import RichLogScreen


class TestTuiLogging(TuiBase):

    @pytest.mark.asyncio
    async def test_logging(self, setup_project_paths):
        """
        Test logging by running some commands, checking they
        are displayed on the logging tree, that the most recent
        log is correct and that the log screen opens when clicked.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            # Update configs and create folders to make some logs
            project = DataShuttle(project_name)
            project.update_config_file(overwrite_old_files=True)

            await pilot.pause(5)  # small delay to ensure order of logs
            project.create_folders("sub-001")

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            # Open the logging tab and check the logs are shown in
            # the correct filetree nodes
            await self.switch_tab(pilot, "logging")

            await self.reload_tree_nodes(
                pilot, "#logging_tab_custom_directory_tree", 2
            )

            logging_tab = pilot.app.screen.query_one("#tabscreen_logging_tab")

            assert (
                "update-config-file"
                in pilot.app.screen.query_one(
                    "#logging_tab_custom_directory_tree"
                )
                .get_node_at_line(1)
                .data.path.stem
            )
            assert (
                "create-folders"
                in pilot.app.screen.query_one(
                    "#logging_tab_custom_directory_tree"
                )
                .get_node_at_line(2)
                .data.path.stem
            )

            # Check the latest logging path is correct
            assert (
                pilot.app.screen.interface.project.get_logging_path()
                == logging_tab.latest_log_path.parent
            )
            assert "create-folders" in logging_tab.latest_log_path.stem
            assert (
                "create-folders"
                in logging_tab.query_one(
                    "#logging_most_recent_label"
                ).renderable._text[0]
            )

            # Check log screen shows on button click
            await self.scroll_to_click_pause(
                pilot, "#logging_tab_open_most_recent_button"
            )

            assert isinstance(pilot.app.screen, RichLogScreen)

            await pilot.pause()
