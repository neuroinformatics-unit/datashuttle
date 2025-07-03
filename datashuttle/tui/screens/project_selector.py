from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.app import TuiApp

from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Header

from datashuttle.tui.interface import Interface
from datashuttle.utils.getters import (
    get_existing_project_paths,
)


class ProjectSelectorScreen(Screen):
    """The project selection screen.

    Finds and displays DataShuttle projects present on the local system.

    `self.dismiss()` returns an initialised project if initialisation
    was successful. Otherwise, in case `Main Menu` button is pressed,
    returns None to return without effect to the main menu.,

    Parameters
    ----------
    mainwindow
        The main TUI app, functions on which are used to coordinate
        screen display.

    """

    TITLE = "Select Project"

    def __init__(self, mainwindow: TuiApp) -> None:
        """Initialise the ProjectSelectorScreen."""
        super(ProjectSelectorScreen, self).__init__()

        self.project_names = [
            path_.stem for path_ in get_existing_project_paths()
        ]
        self.mainwindow = mainwindow

    def compose(self) -> ComposeResult:
        """Add widgets to the ProjectSelectorScreen."""
        yield Header(id="project_select_header")
        yield Button("Main Menu", id="all_main_menu_buttons")
        yield Container(
            *[
                Button(name, id=self.name_to_id(name))
                for name in self.project_names
            ],
            id="project_select_top_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on ProjectSelectorScreen."""
        project_name = self.id_to_name(event.button.id)

        if project_name in self.project_names:
            interface = Interface()
            success, output = interface.select_existing_project(project_name)

            if success:
                self.dismiss(interface)
            else:
                self.mainwindow.show_modal_error_dialog(output)

        elif event.button.id == "all_main_menu_buttons":
            self.dismiss(False)

    @staticmethod
    def name_to_id(name: str):
        """Convert the project name to a textual ID.

        Textual ids cannot start with a number, so ensure
        all ids are prefixed with text instead of the project name.
        """
        return f"safety_prefix_{name}"

    @staticmethod
    def id_to_name(id: str):
        """See `name_to_id()`."""
        return id[len("safety_prefix_") :]
