import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.tabs.logging import RichLogScreen

from .. import test_utils
from .tui_base import TuiBase


class TestTuiLogging(TuiBase):
    @pytest.mark.asyncio
    async def test_logging(self, setup_project_paths):
        """Test logging by running some commands, checking they
        are displayed on the logging tree, that the most recent
        log is correct and that the log screen opens when clicked.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Update configs and create folders to make some logs
            project = test_utils.make_project(project_name)

            # Sometimes in CI environment there is already an
            # update-config-file log here. Not sure why, it's not
            # been seen to occur outside and CI and happens randomly
            # across builds in CI.
            for file in project.get_logging_path().glob("*.log"):
                file.unlink()

            project.update_config_file(central_host_username="username")

            await pilot.pause(5)

            project.create_folders("rawdata", "sub-001")

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
            widg = pilot.app.screen.query_one(
                "#logging_tab_custom_directory_tree"
            )
            assert (
                "create-folders" in widg.get_node_at_line(2).data.path.stem
            ), (
                f"ERROR MESSAGE: {widg.get_node_at_line(0).data.path}-{widg.get_node_at_line(1).data.path}-{widg.get_node_at_line(2).data.path}"
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
                ).renderable
            )

            # Check log screen shows on button click
            await self.scroll_to_click_pause(
                pilot, "#logging_tab_open_most_recent_button"
            )

            assert isinstance(pilot.app.screen, RichLogScreen)

            await pilot.pause()
