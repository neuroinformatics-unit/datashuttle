import os

from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RichLog, TabPane

from datashuttle.tui.custom_widgets import (
    CustomDirectoryTree,
)
from datashuttle.tui.utils.tui_decorators import require_double_click


class RichLogScreen(ModalScreen):
    def __init__(self, log_file):
        super(RichLogScreen, self).__init__()

        with open(log_file, "r") as file:
            self.log_contents = "".join(file.readlines())

    def compose(self):
        yield RichLog(highlight=True, markup=True)
        yield Button("Close", id="rich_log_screen_close_button")

    def on_mount(self):
        text_log = self.query_one(RichLog)
        text_log.write(self.log_contents)

    def on_button_pressed(self, event):
        if event.button.id == "rich_log_screen_close_button":
            self.dismiss()


class LoggingTab(TabPane):
    def __init__(self, title, mainwindow, project, id):
        super(LoggingTab, self).__init__(title=title, id=id)

        self.mainwindow = mainwindow
        self.project = project

        # Hold the latest logs on this variable to ensure
        # display and functionality are always in sync.
        self.latest_log_path = None
        self.update_latest_log_path()
        self.prev_click_time = 0

    def update_latest_log_path(self):
        logs = self.project.get_logging_path().glob("*.log")
        self.latest_log_path = max(logs, key=os.path.getctime)

    def compose(self):
        yield Label("Double click logging file to select")
        yield CustomDirectoryTree(
            self.mainwindow,
            self.project.get_logging_path(),
            id="logging_tab_custom_directory_tree",
        )
        yield Label("or select most recent:")
        yield Horizontal(
            Button(
                "Open Most Recent", id="logging_tab_open_most_recent_button"
            ),
            Label(f"{self.latest_log_path.stem}"),
        )

    def on_button_pressed(self, event):
        if event.button.id == "logging_tab_open_most_recent_button":
            self.push_rich_log_screen(self.latest_log_path)

    @require_double_click
    def on_directory_tree_file_selected(self, node):
        if not node.path.is_file():
            self.mainwindow.show_modal_error_dialog(
                "Log file no longer exists. Refresh the directory tree"
                "by pressing CTRL and r at the same time."
            )
            return

        self.push_rich_log_screen(node.path)

    def push_rich_log_screen(self, log_path):
        self.mainwindow.push_screen(
            RichLogScreen(
                log_path,
            )
        )

    def reload_directorytree(self):
        self.query_one("#logging_tab_custom_directory_tree").reload()

    # TODO: look into this, should handle on the directorytree itself... dam this sucks!
    def on_custom_directory_tree_directory_tree_special_key_press(self):
        self.reload_directorytree()
