from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.app import App

from textual.screen import Screen
from textual.widgets import Button, Header

from datashuttle.tui.shared import validate_content


class ValidateScreen(Screen):
    """
    Screen for setting up a new datashuttle project, by
    inputting the desired configs. This uses the
    ConfigsContent window to display and set the configs.

    If "Main Manu" button is pressed, the callback function
    returns None, so the project screen is not switched to.

    Otherwise, the logic for creating and validating the
    project is in ConfigsContent. ConfigsContent calls
    the dismiss method of this class to return
    an initialised project to mainwindow.
    See ConfigsContent.on_button_pressed() for more details

    Parameters
    ----------

    mainwindow : TuiApp
    """

    TITLE = "Validate Project"

    def __init__(self, mainwindow: App) -> None:
        super(ValidateScreen, self).__init__()

        self.mainwindow = mainwindow

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Main Menu", id="all_main_menu_buttons")
        yield validate_content.ValidateContent(
            self, interface=None, id="validate_from_path_content"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "all_main_menu_buttons":
            self.dismiss(None)
