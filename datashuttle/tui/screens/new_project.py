from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.app import TuiApp

from textual.screen import Screen
from textual.widgets import Button, Header

from datashuttle.tui.shared import configs_content


class NewProjectScreen(Screen):
    """Screen for setting up a new datashuttle project.

    If "Main Manu" button is pressed, the callback function
    returns None, so the project screen is not switched to.

    Otherwise, the logic for creating and validating the
    project is in ConfigsContent. ConfigsContent calls
    the dismiss method of this class to return
    an initialised project to mainwindow.

    Parameters
    ----------
    mainwindow
        The main TUI app

    """

    TITLE = "Make New Project"

    def __init__(self, mainwindow: TuiApp) -> None:
        """Initialise the NewProjectScreen."""
        super(NewProjectScreen, self).__init__()

        self.mainwindow = mainwindow

    def compose(self) -> ComposeResult:
        """Add widgets to the NewProjectScreen."""
        yield Header()
        yield Button("Main Menu", id="all_main_menu_buttons")
        yield configs_content.ConfigsContent(
            self, interface=None, id="new_project_configs_content"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on the NewProjectScreen."""
        if event.button.id == "all_main_menu_buttons":
            self.dismiss(None)
