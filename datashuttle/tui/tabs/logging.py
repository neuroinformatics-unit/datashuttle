from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual import events
    from textual.app import ComposeResult
    from textual.widgets import DirectoryTree

    from datashuttle import DataShuttle
    from datashuttle.tui.app import TuiApp

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RichLog, TabPane

from datashuttle.tui.custom_widgets import (
    CustomDirectoryTree,
)
from datashuttle.tui.utils.tui_decorators import (
    ClickInfo,
    require_double_click,
)


class RichLogScreen(ModalScreen):
    """Screen to display the log output."""

    def __init__(self, log_file):
        """Initialise the RichLogScreen."""
        super(RichLogScreen, self).__init__()

        with open(log_file) as file:
            self.log_contents = "".join(file.readlines())

    def compose(self) -> ComposeResult:
        """Set the widgets for the screen."""
        yield Container(
            RichLog(highlight=True, markup=True, id="richlog_screen_rich_log"),
            Button("Close", id="richlog_screen_close_button"),
        )

    def on_mount(self) -> None:
        """Update widgets immediately after mount."""
        text_log = self.query_one(RichLog)
        text_log.write(self.log_contents)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on the screen."""
        if event.button.id == "richlog_screen_close_button":
            self.dismiss()


class LoggingTab(TabPane):
    """The logging tab on the project manager screen."""

    def __init__(
        self, title: str, mainwindow: TuiApp, project: DataShuttle, id: str
    ):
        """Initialise the Logging Tab.

        Parameters
        ----------
        title
            Title for the tab.

        mainwindow
            Tui main appl

        project
            DataShuttle project.

        id
            Textual ID for the LoggingTab.

        """
        super(LoggingTab, self).__init__(title=title, id=id)

        self.mainwindow = mainwindow
        self.project = project

        # Hold the latest logs on this variable to ensure
        # display and functionality are always in sync.
        self.latest_log_path = None
        self.update_latest_log_path()
        self.click_info = ClickInfo()

    def update_latest_log_path(self):
        """Set the `latest_log_path` attribute that can be opened through a button."""
        logs = list(self.project.get_logging_path().glob("*.log"))
        self.latest_log_path = (
            max(logs, key=os.path.getctime)
            if any(logs)
            else Path("None found.")
        )

    def compose(self) -> ComposeResult:
        """Set with widgets on the LoggingTab."""
        yield Container(
            Label(
                "Double click logging file to select:",
                id="logging_tab_top_label",
            ),
            CustomDirectoryTree(
                self.mainwindow,
                self.project.get_logging_path(),
                id="logging_tab_custom_directory_tree",
            ),
            Label(
                "",
                id="logging_most_recent_label",
            ),
            Horizontal(
                Button(
                    "Open Most Recent",
                    id="logging_tab_open_most_recent_button",
                ),
            ),
            id="logging_tab_outer_container",
        )

    def _on_mount(self, event: events.Mount) -> None:
        """Update the widgets immediately after mounting."""
        self.update_most_recent_label()

    def update_most_recent_label(self):
        """Update the label indicating the most recently saved log."""
        self.update_latest_log_path()
        self.query_one("#logging_most_recent_label").update(
            f"or open most recent: {self.latest_log_path.stem}"
        )
        self.refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press on the tab."""
        if event.button.id == "logging_tab_open_most_recent_button":
            self.push_rich_log_screen(self.latest_log_path)

    @require_double_click
    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle a click on the DirectoryTree showing the log files."""
        if not event.path.is_file():
            self.mainwindow.show_modal_error_dialog(
                "Log file no longer exists. Refresh the directory tree"
                "by pressing CTRL and r at the same time."
            )
            return

        self.push_rich_log_screen(event.path)

    def push_rich_log_screen(self, log_path):
        """Push the screen that displays the log file contents."""
        self.mainwindow.push_screen(
            RichLogScreen(
                log_path,
            )
        )

    def reload_directorytree(self) -> None:
        """Refresh the DirectoryTree (e.g. if a new log file is saved)."""
        self.query_one("#logging_tab_custom_directory_tree").reload()

    def on_custom_directory_tree_directory_tree_special_key_press(
        self,
    ) -> None:
        """Handle the CTRL+R refresh of the directory tree."""
        self.reload_directorytree()
