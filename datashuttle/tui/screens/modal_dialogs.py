from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult

    from datashuttle.tui.app import App

from pathlib import Path

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from datashuttle.tui.custom_widgets import CustomDirectoryTree
from datashuttle.tui.utils.tui_decorators import require_double_click


class MessageBox(ModalScreen):
    """
    A screen for rendering error messages.

    message : str
        The message to display in the message box

    border_color : str
        The color to pass to the `border` style on the widget. Note that the
        keywords 'red' and 'green' are overridden for custom style.
    """

    def __init__(self, message: str, border_color: str) -> None:
        super(MessageBox, self).__init__()

        self.message = message
        self.border_color = border_color

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Static(self.message, id="messagebox_message_label"),
                id="messagebox_message_container",
            ),
            Container(Button("OK"), id="messagebox_ok_button"),
            id="messagebox_top_container",
        )

    def on_mount(self) -> None:
        if self.border_color == "red":
            color = "rgb(140, 12, 0)"
        elif self.border_color == "green":
            color = "rgb(1, 138, 13)"
        else:
            color = self.border_color

        self.query_one("#messagebox_top_container").styles.border = (
            "thick",
            color,
        )

    def on_button_pressed(self) -> None:
        self.dismiss(True)


class ConfirmScreen(ModalScreen):
    """
    A screen for rendering confirmation messages.
    """

    def __init__(self, message: str) -> None:
        super().__init__()

        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.message, id="confirm_message_label"),
            Horizontal(
                Button("Yes", id="confirm_ok_button"),
                Button("No", id="confirm_cancel_button"),
                id="confirm_button_container",
            ),
            id="confirm_top_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_ok_button":
            self.dismiss(True)
        else:
            self.dismiss(False)


class SelectDirectoryTreeScreen(ModalScreen):
    """
    A modal screen that includes a DirectoryTree to browse
    and select folders. If a folder is double-clicked,
    the path to the folder is returned through 'dismiss'
    callback mechanism.

    Parameters
    ----------

    mainwindow : App
        Textual main app screen

    path_ : Optional[Path]
        Path to use as the DirectoryTree root,
        if `None` set to the system user home.
    """

    def __init__(self, mainwindow: App, path_: Optional[Path] = None) -> None:
        super(SelectDirectoryTreeScreen, self).__init__()
        self.mainwindow = mainwindow

        if path_ is None:
            path_ = Path().home()
        self.path_ = path_

        self.prev_click_time = 0

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Double click a folder to select:", id="test_label"),
            CustomDirectoryTree(
                self.mainwindow,
                self.path_,
                id="select_directory_tree_directory_tree",
            ),
            Button("Cancel", id="cancel_button"),
            id="select_directory_tree_container",
        )

    @require_double_click
    def on_directory_tree_directory_selected(self, node) -> None:
        if node.path.is_file():
            return
        else:
            self.dismiss(node.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_button":
            self.dismiss(False)
