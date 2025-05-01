from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.app import TuiApp

from textual.screen import Screen
from textual.widgets import Button, Header

from datashuttle.tui.shared import validate_content


class ValidateScreen(Screen):
    """
    Screen to hold the validation window for
    validating an existing project at a given path.
    All widgets are stored in `ValidateContent`, which is
    shared between here and the validation tab on the project manager.
    """

    TITLE = "Validate Project"

    def __init__(self, mainwindow: TuiApp) -> None:
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
