import platform
from pathlib import Path

import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import (
    SelectDirectoryTreeScreen,
)


@pytest.mark.asyncio
async def test_select_directory_tree(monkeypatch):
    """
    Test that changing the drive in SelectDirectoryTreeScreen
    updates the DirectoryTree path as expected.
    """

    # Set up fake and real drives
    actual_drive = (
        str(Path.home().drive) if platform.system() == "Windows" else "/"
    )
    fake_drive = "Z:\\" if platform.system() == "Windows" else "/mnt/fake"

    monkeypatch.setattr(
        SelectDirectoryTreeScreen,
        "get_drives",
        staticmethod(
            lambda: [(actual_drive, actual_drive), (fake_drive, fake_drive)]
        ),
    )

    app = TuiApp()
    async with app.run_test(size=(200, 100)) as pilot:

        await pilot.click("#mainwindow_new_project_button")

        await pilot.click("#configs_local_path_select_button")
        assert isinstance(pilot.app.screen, SelectDirectoryTreeScreen)

        tree = pilot.app.screen.query_one(
            "#select_directory_tree_directory_tree"
        )
        select = pilot.app.screen.query_one(
            "#select_directory_tree_drive_select"
        )

        while not select.options:
            await pilot.pause(0.5)

        fake_drive_index = next(
            (
                i
                for i, (value, label) in enumerate(select.options)
                if value == fake_drive
            ),
            None,
        )
        if fake_drive_index is not None:
            select.selected_index = fake_drive_index
            await pilot.pause()
            assert str(tree.path) == fake_drive

        actual_drive_index = next(
            (
                i
                for i, (value, label) in enumerate(select.options)
                if value == actual_drive
            ),
            None,
        )
        if actual_drive_index is not None:
            select.selected_index = actual_drive_index
            await pilot.pause()
            assert str(tree.path) == actual_drive
