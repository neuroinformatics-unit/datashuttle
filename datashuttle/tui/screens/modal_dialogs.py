from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.app import TuiApp
    from datashuttle.utils.custom_types import InterfaceOutput

import platform
from pathlib import Path

import psutil
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    LoadingIndicator,
    Select,
    Static,
)

from datashuttle.tui.custom_widgets import CustomDirectoryTree
from datashuttle.tui.utils.tui_decorators import require_double_click


class MessageBox(ModalScreen):
    """
    A screen for rendering error messages.

    message : str
        The message to display in the message box

    border_color : str
        The color to pass to the `border` style on the widget. Note that the
        keywords 'red' 'grey' 'green' are overridden for custom style.
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
        elif self.border_color in ["gray", "grey"]:
            color = "rgb(184, 184, 184)"
        else:
            color = self.border_color

        self.query_one("#messagebox_top_container").styles.border = (
            "thick",
            color,
        )

    def on_button_pressed(self) -> None:
        self.dismiss(True)


class ConfirmAndAwaitTransferPopup(ModalScreen):
    """
    A popup screen for confirming, awaiting and finishing a Transfer.

    When users select Transfer, this screen pops up to a) allow users to confirm transfer b) display
    a `LoadingIndicator` while the transfer runs in a separate worker c) indicate the transfer is finished.
    It is much easier to handle this on a single screen, rather than open / close screens at each stage.
    """

    def __init__(
        self,
        message: str,
        transfer_func: Callable[[], Worker[InterfaceOutput]],
    ) -> None:
        super().__init__()

        self.transfer_func = transfer_func
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
            self.query_one("#confirm_button_container").remove()

            # Start the data transfer
            asyncio.create_task(
                self.handle_transfer_and_update_ui_when_complete(),
                name="data_transfer_async_task",
            )

            self.query_one("#confirm_message_label").update("Transferring...")
            loading_indicator = LoadingIndicator(id="loading_indicator")
            self.query_one("#confirm_top_container").mount(loading_indicator)
        else:
            self.dismiss()

    async def handle_transfer_and_update_ui_when_complete(self) -> None:
        """Runs the data transfer worker and updates the UI on completion"""

        data_transfer_worker = self.transfer_func()
        await data_transfer_worker.wait()
        success, output = data_transfer_worker.result
        self.dismiss()

        if success:
            self.app.push_screen(
                MessageBox(
                    "Transfer finished."
                    "\n\n"
                    "Check the most recent logs to "
                    "ensure transfer completed successfully.",
                    border_color="grey",
                )
            )
        else:
            self.app.show_modal_error_dialog(output)


class SelectDirectoryTreeScreen(ModalScreen):
    """
    A modal screen that includes a DirectoryTree to browse
    and select folders. If a folder is double-clicked,
    the path to the folder is returned through 'dismiss'
    callback mechanism.

    Parameters
    ----------

    mainwindow : TuiApp
        Textual main app screen

    path_ : Optional[Path]
        Path to use as the DirectoryTree root,
        if `None` set to the system user home.
    """

    def __init__(
        self, mainwindow: TuiApp, path_: Optional[Path] = None
    ) -> None:
        super(SelectDirectoryTreeScreen, self).__init__()
        self.mainwindow = mainwindow

        if path_ is None:
            path_ = Path().home()
        self.path_ = path_

        if platform.system() == "Windows":
            self.selected_drive = self.path_.drive + "\\"
        else:
            self.selected_drive = "/"
        self.prev_click_time = 0

    def compose(self) -> ComposeResult:

        label_message = (
            "Select (double click) a folder with the same name as the project.\n"
            "If the project folder does not exist, select the parent folder and it will be created."
        )

        drives = self.get_drives()

        yield Container(
            Static(label_message, id="select_directory_tree_screen_label"),
            Select(  # Dropdown for drives
                [(drive, drive) for drive in self.get_drives()],
                value=self.selected_drive if self.selected_drive in drives else drives[0],
                allow_blank=False,
                id="select_directory_tree_drive_select",
            ),
            CustomDirectoryTree(
                self.mainwindow,
                self.path_,
                id="select_directory_tree_directory_tree",
            ),
            Button("Cancel", id="cancel_button"),
            id="select_directory_tree_container",
        )

    @staticmethod
    def get_drives():
        operating_system = platform.system()
    
        assert operating_system in ["Windows", "Darwin", "Linux"], \
            f"Unexpected operating system: {operating_system} encountered"
        
        if platform.system() == "Windows":
            return [disk.device for disk in psutil.disk_partitions(all=False)]

        elif platform.system() in ["Darwin", "Linux"]:
            return ["/"] + [
                f"/{dir.name}" for dir in Path("/").iterdir() if dir.is_dir()
            ]

    def on_select_changed(self, event: Select.Changed) -> None:
        """Updates the directory tree when the drive is changed."""
        self.path_ = Path(event.value)
        self.query_one("#select_directory_tree_directory_tree").path = (
            self.path_
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


class RenameFileOrFolderScreen(ModalScreen):
    """ """

    def __init__(self, mainwindow: TuiApp, path_: Path) -> None:
        super(RenameFileOrFolderScreen, self).__init__()

        self.mainwindow = mainwindow
        self.path_ = path_

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Input the new name:", id="rename_screen_label"),
            Input(value=self.path_.stem, id="rename_screen_input"),
            Horizontal(
                Button("Ok", id="rename_screen_okay_button"),
                Button("Cancel", id="rename_screen_cancel_button"),
                id="rename_screen_horizontal",
            ),
            id="rename_screen_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """"""
        if event.button.id == "rename_screen_okay_button":
            self.dismiss(self.query_one("#rename_screen_input").value)

        elif event.button.id == "rename_screen_cancel_button":
            self.dismiss(False)
