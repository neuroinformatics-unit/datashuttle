from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult
    from textual.widgets import DirectoryTree
    from textual.worker import Worker

    from datashuttle.tui.app import TuiApp
    from datashuttle.utils.custom_types import InterfaceOutput, Prefix

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
from datashuttle.tui.utils.tui_decorators import (
    ClickInfo,
    require_double_click,
)


class MessageBox(ModalScreen):
    """A screen for rendering error messages.

    Parameters
    ----------
    message
        The message to display in the message box

    border_color
        The color to pass to the `border` style on the widget. Note that the
        keywords 'red' 'grey' 'green' are overridden for custom style.

    """

    def __init__(self, message: str, border_color: str) -> None:
        """Initialise the MessageBox.

        Parameters
        ----------
        message
            Message to display on the MessageBox.

        border_color
            Color of the MessageBox border (e.g. green if the message is positive).

        """
        super(MessageBox, self).__init__()

        self.message = message
        self.border_color = border_color

    def compose(self) -> ComposeResult:
        """Add widgets to the MessageBox."""
        yield Container(
            Container(
                Static(self.message, id="messagebox_message_label"),
                id="messagebox_message_container",
            ),
            Container(Button("OK"), id="messagebox_ok_button"),
            id="messagebox_top_container",
        )

    def on_mount(self) -> None:
        """Update widgets immediately after mounting."""
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
        """Handle button press."""
        self.dismiss(True)


class ConfirmAndAwaitTransferPopup(ModalScreen):
    """A popup screen for confirming, awaiting and finishing a Transfer.

    When users select Transfer, this screen pops up to a) allow users to confirm transfer b) display
    a `LoadingIndicator` while the transfer runs in a separate worker c) indicate the transfer is finished.
    It is much easier to handle this on a single screen, rather than open / close screens at each stage.
    """

    def __init__(
        self,
        message: str,
        transfer_func: Callable[[], Worker[InterfaceOutput]],
    ) -> None:
        """Initialise the ConfirmAndAwaitTransferPopup.

        Parameters
        ----------
        message
            Message to display while running the transfer.

        transfer_func
            Function to run in a worker that performs the transfer.

        """
        super().__init__()

        self.transfer_func = transfer_func
        self.message = message

    def compose(self) -> ComposeResult:
        """Add widgets to the ConfirmAndAwaitTransferPopup."""
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
        """Handle button press on the ConfirmAndAwaitTransferPopup."""
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
        """Run the data transfer worker and updates the UI on completion."""
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


class SearchingCentralForNextSubSesPopup(ModalScreen):
    """Show message and a loading indicator for suggesting the next subject or session.

    Used to await searching next sub/ses across including folders
    present on the central machine. This search happens in a separate
    thread to allow TUI to display the loading indicate without freezing.

    Only displayed when the `include_central` flag is checked and the
    connection method is "ssh".
    """

    def __init__(self, sub_or_ses: Prefix) -> None:
        """Initialise SearchingCentralForNextSubSesPopup."""
        super().__init__()
        self.message = f"Searching central for next {sub_or_ses}"

    def compose(self) -> ComposeResult:
        """Add widgets to SearchingCentralForNextSubSesPopup."""
        yield Container(
            Label(self.message, id="searching_message_label"),
            LoadingIndicator(id="searching_animated_indicator"),
            id="searching_top_container",
        )


class SelectDirectoryTreeScreen(ModalScreen):
    """Screen that includes a DirectoryTree to browse and select folders.

    If a folder is double-clicked, the path to the folder is
    returned through 'dismiss' callback mechanism.

    Parameters
    ----------
    mainwindow
        Textual main app screen

    path_
        Path to use as the DirectoryTree root,
        if `None` set to the system user home.

    """

    def __init__(
        self, mainwindow: TuiApp, path_: Optional[Path] = None
    ) -> None:
        """Initialise SelectDirectoryTreeScreen.

        Parameters
        ----------
        mainwindow
            The main TUI app.

        path_
            Root path for the DirectoryTree.

        """
        super(SelectDirectoryTreeScreen, self).__init__()
        self.mainwindow = mainwindow

        if path_ is None:
            path_ = Path().home()
        self.path_ = path_

        self.click_info = ClickInfo()

    def compose(self) -> ComposeResult:
        """Add widgets to the SelectDirectoryTreeScreen."""
        label_message = (
            "Select (double click) a folder with the same name as the project.\n"
            "If the project folder does not exist, select the parent folder and it will be created."
        )

        yield Container(
            Static(label_message, id="select_directory_tree_screen_label"),
            Select(
                [(drive, drive) for drive in self.get_drives()],
                value=self.get_selected_drive(),
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
    def get_drives() -> list[str]:
        """Return drives available on the machine to switch between.

        For Windows,  use `psutil` to get the list of drives.
        Otherwise, assume root is "/" and take all folders from that level.
        """
        operating_system = platform.system()

        assert operating_system in [
            "Windows",
            "Darwin",
            "Linux",
        ], f"Unexpected operating system: {operating_system} encountered."

        if platform.system() == "Windows":
            return [disk.device for disk in psutil.disk_partitions(all=True)]

        else:
            return ["/"] + [
                f"/{dir.name}" for dir in Path("/").iterdir() if dir.is_dir()
            ]

    def get_selected_drive(self) -> str:
        """Return the default drive which the select starts on.

        For windows, use the .drive attribute but for macOS and Linux
        this is blank. On these Os use the first folder (e.g. /Users)
        as the default drive.
        """
        if platform.system() == "Windows":
            selected_drive = f"{self.path_.drive}\\"
        else:
            selected_drive = f"/{self.path_.parts[1]}"

        return selected_drive

    def on_select_changed(self, event: Select.Changed) -> None:
        """Update the directory tree when the drive is changed."""
        self.path_ = Path(event.value)
        self.query_one(
            "#select_directory_tree_directory_tree"
        ).path = self.path_

    @require_double_click
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle a node on the DirectoryTree selected."""
        if event.path.is_file():
            return
        else:
            self.dismiss(event.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel button pressed."""
        if event.button.id == "cancel_button":
            self.dismiss(False)


class RenameFileOrFolderScreen(ModalScreen):
    """A screen to handle the renaming of a file or folder selected through the DirectoryTree."""

    def __init__(self, mainwindow: TuiApp, path_: Path) -> None:
        """Initialise RenameFileOrFolderScreen.

        Parameters
        ----------
        mainwindow
            The main TUI app.

        path_
            Path of the file or folder to rename.

        """
        super(RenameFileOrFolderScreen, self).__init__()

        self.mainwindow = mainwindow
        self.path_ = path_

    def compose(self) -> ComposeResult:
        """Add widgets to the RenameFileOrFolderScreen."""
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
        """Handle button pressed on the RenameFileOrFolderScreen."""
        if event.button.id == "rename_screen_okay_button":
            self.dismiss(self.query_one("#rename_screen_input").value)

        elif event.button.id == "rename_screen_cancel_button":
            self.dismiss(False)
