import pytest
from pathlib import Path
import platform
from tui_base import TuiBase
from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import (
    SelectDirectoryTreeScreen,
)


class TestSelectTree(TuiBase):
    @pytest.mark.asyncio
    async def test_select_directory_tree(self, monkeypatch):
        """
        Test that changing the drive in SelectDirectoryTreeScreen
        updates the DirectoryTree path as expected.
        """

        Drive1= str(Path.home().drive) if platform.system() == "Windows" else "/"
        Drive2 = "Z:\\" if platform.system() == "Windows" else "/mnt/fake"

        monkeypatch.setattr(
            SelectDirectoryTreeScreen,
            "get_drives",
            staticmethod(lambda: ["Drive1", "Drive2"]),
        )

        app = TuiApp()
        async with app.run_test(size=(200,100)) as pilot:

            await self.scroll_to_click_pause(pilot,"#mainwindow_new_project_button")

            await self.scroll_to_click_pause(pilot,"#configs_local_path_select_button")
            assert isinstance(pilot.app.screen, SelectDirectoryTreeScreen)

            tree = pilot.app.screen.query_one("#select_directory_tree_directory_tree")
            select = pilot.app.screen.query_one("#select_directory_tree_drive_select")


            select.value = "Drive1"
            await pilot.pause()
            assert str(tree.path) == "Drive1"

            select.value = "Drive2"
            await pilot.pause()
            assert str(tree.path) == "Drive2"
