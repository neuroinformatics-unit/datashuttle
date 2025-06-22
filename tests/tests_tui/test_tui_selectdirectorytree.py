import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import (
    SelectDirectoryTreeScreen,
)

from .tui_base import TuiBase


class TestSelectTree(TuiBase):
    @pytest.mark.asyncio
    async def test_select_directory_tree(self, monkeypatch):
        """Test that changing the drive in SelectDirectoryTreeScreen
        updates the DirectoryTree path as expected.
        """
        # Set the Select drives to be these test cases
        monkeypatch.setattr(
            SelectDirectoryTreeScreen,
            "get_selected_drive",
            staticmethod(lambda: "Drive1"),
        )

        monkeypatch.setattr(
            SelectDirectoryTreeScreen,
            "get_drives",
            staticmethod(lambda: ["Drive1", "Drive2"]),
        )

        app = TuiApp()
        async with app.run_test() as pilot:
            # Open the select directory tree screen
            await self.scroll_to_click_pause(
                pilot, "#mainwindow_new_project_button"
            )

            await self.scroll_to_click_pause(
                pilot, "#configs_local_path_select_button"
            )
            assert isinstance(pilot.app.screen, SelectDirectoryTreeScreen)

            # Switch the select, and ensure the directory tree is updated as expected
            tree = pilot.app.screen.query_one(
                "#select_directory_tree_directory_tree"
            )
            select = pilot.app.screen.query_one(
                "#select_directory_tree_drive_select"
            )

            select.value = "Drive1"
            await pilot.pause()
            assert str(tree.path) == "Drive1"

            select.value = "Drive2"
            await pilot.pause()
            assert str(tree.path) == "Drive2"
