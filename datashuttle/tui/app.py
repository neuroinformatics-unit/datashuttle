from __future__ import annotations

import os
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from datashuttle.tui.interface import Interface

from pathlib import Path

import pyperclip
import showinfm
import yaml
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import (
    Button,
    Label,
)

from datashuttle.configs import canonical_folders
from datashuttle.tui.screens import (
    get_help,
    modal_dialogs,
    new_project,
    project_manager,
    project_selector,
    settings,
    validate_at_path,
)
from datashuttle.tui.tooltips import get_tooltip


class TuiApp(App, inherit_bindings=False):  # type: ignore
    """The main app page for the DataShuttle TUI.

    This class acts as a base class from which all windows
    (select existing project, make new project, settings and
    get help) are raised.
    """

    tui_path = Path(__file__).parent
    CSS_PATH = list(Path(tui_path / "css").glob("*.tcss"))
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+c", "app.quit", "Exit app", priority=True),
    ]

    def compose(self) -> ComposeResult:
        """Set up widgets for the main window."""
        yield Container(
            Label("datashuttle", id="mainwindow_banner_label"),
            Button(
                "Select Existing Project",
                id="mainwindow_existing_project_button",
            ),
            Button("Make New Project", id="mainwindow_new_project_button"),
            Button(
                "Validate Project at Path",
                id="mainwindow_validate_from_project_path",
            ),
            Button("Settings", id="mainwindow_settings_button"),
            Button("Get Help", id="mainwindow_get_help_button"),
            id="mainwindow_contents_container",
        )

    def on_mount(self) -> None:
        """Update widgets immediately after creation."""
        self.set_dark_mode(self.load_global_settings()["dark_mode"])
        id = "#mainwindow_validate_from_project_path"
        self.query_one(id).tooltip = get_tooltip(id)

    def set_dark_mode(self, dark_mode: bool) -> None:
        """Set the color theme for the application."""
        self.theme = "textual-dark" if dark_mode else "textual-light"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on the main window and raise a new screen.

        Note that`push_screen` second argument is a callback function returned
        after screen closes.

        Parameters
        ----------
        event
            A textual event containing information about the  button press.

        """
        if event.button.id == "mainwindow_existing_project_button":
            self.push_screen(
                project_selector.ProjectSelectorScreen(self),
                self.load_project_page,
            )

        elif event.button.id == "mainwindow_new_project_button":
            self.push_screen(
                new_project.NewProjectScreen(self),
                self.load_project_page,
            )

        elif event.button.id == "mainwindow_settings_button":
            self.push_screen(
                settings.SettingsScreen(
                    self,
                )
            )

        elif event.button.id == "mainwindow_get_help_button":
            self.push_screen(get_help.GetHelpScreen())

        elif event.button.id == "mainwindow_validate_from_project_path":
            self.push_screen(validate_at_path.ValidateScreen(self))

    def load_project_page(self, interface: Interface) -> None:
        """Load the project manager page.

        This page contains a list of all existing projects.

        Parameters
        ----------
        interface
            Datashuttle tui Interface object.

        """
        if interface:
            self.push_screen(
                project_manager.ProjectManagerScreen(
                    self, interface, id="project_manager_screen"
                )
            )

    def show_modal_error_dialog(self, message: str) -> None:
        """Show an error in a pop-up window.

        The pop-up window has a red border and is modal (cannot click
        elsewhere on the application when it is shown).

        Parameter
        ---------
        message
            Error message to display.
        """
        self.push_screen(modal_dialogs.MessageBox(message, border_color="red"))

    def show_modal_error_dialog_from_main_thread(self, message: str) -> None:
        """Call`show_modal_error_dialog from main thread when executing in another thread."""
        self.call_from_thread(self.show_modal_error_dialog, message)

    def handle_open_filesystem_browser(self, path_: Path) -> None:
        """Open the system file browser to the path with the `showinfm` package."""
        if not path_.exists():
            self.show_modal_error_dialog(
                f"{path_.as_posix()} cannot be opened as it "
                f"does not exist on the filesystem."
            )
            return

        try:
            showinfm.show_in_file_manager(path_.as_posix())
        except BaseException:
            if path_.is_file():
                # I don't see why this is not working as according to docs it
                # should open the containing folder and select.
                message = (
                    "Could not open file. Only folders can be "
                    "opened in the filesystem browser."
                )
            else:
                message = (
                    "Unexpected error occurred. Please contact the datashuttle"
                    "development team."
                )

            self.show_modal_error_dialog(message)

    def prompt_rename_file_or_folder(self, path_) -> None:
        """Display pop-up window to rename a file or folder in a tab DirectoryTree.

        Parameters
        ----------
        path_
            Path to the file or folder to rename.

        TODO
        ----
        Can this not be moved to the relevant tab page?

        """
        self.push_screen(
            modal_dialogs.RenameFileOrFolderScreen(self, path_),
            lambda new_name: self.rename_file_or_folder(path_, new_name),
        )

    def rename_file_or_folder(self, path_, new_name) -> None:
        """Rename a file or folder within the project.

        Parameters
        ----------
        path_
            Path to the file or folder to rename.

        new_name
            New name for the file or folder.

        """
        if new_name is False:
            return
        try:
            if path_.is_dir():
                os.rename(
                    path_.as_posix(), (path_.parent / new_name).as_posix()
                )
            else:
                os.rename(
                    path_.as_posix(),
                    path_.parent / f"{new_name}{path_.suffix}",
                )
            assert isinstance(
                self.screen, project_manager.ProjectManagerScreen
            )
            self.screen.update_active_tab_tree()

        except BaseException as e:
            self.show_modal_error_dialog(
                f"Could not rename the file or folder."
                f"Check the new name is valid, and correct "
                f"permissions are set. \n\n"
                f"Full error log {str(e)}"
            )

    # Global Settings ---------------------------------------------------------

    def load_global_settings(self) -> Dict:
        """Return the loaded 'global settings' for the TUI.

        These settings determine project-independent settings
        that are persistent across sessions. These are stored
        in the canonical .datashuttle folder (see `get_global_settings_path`).
        """
        settings_path = self.get_global_settings_path()

        if not settings_path.is_file():
            global_settings = self.get_default_global_settings()
            self.save_global_settings(global_settings)
        else:
            with open(settings_path) as file:
                global_settings = yaml.full_load(file)

        return global_settings

    def get_global_settings_path(self) -> Path:
        """Return the canonical path for the TUI global settings."""
        path_ = canonical_folders.get_datashuttle_path()
        return path_ / "global_tui_settings.yaml"

    def get_default_global_settings(self) -> Dict:
        """Return placeholder default global settings for the TUI."""
        return {
            "dark_mode": True,
            "show_transfer_tree_status": False,
        }

    def save_global_settings(self, global_settings: Dict) -> None:
        """Save the TUI global settings to disk."""
        settings_path = self.get_global_settings_path()

        if not settings_path.parent.is_dir():
            settings_path.parent.mkdir(parents=True)

        with open(settings_path, "w") as file:
            yaml.dump(global_settings, file, sort_keys=False)

    def copy_to_clipboard(self, value) -> None:
        """Centralized function to copy to clipboard.

        This may fail in headless mode on an HPC.

        Parameters
        ----------
        value
            Value to copy to clipboard.

        """
        try:
            pyperclip.copy(value)
        except pyperclip.PyperclipException:
            self.show_modal_error_dialog(
                "Clipboard copy failed, likely due to operating in headless mode."
            )


def main():
    """Start the application."""
    TuiApp().run()


if __name__ == "__main__":
    main()
