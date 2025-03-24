from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Static,
)


class SetupGoogleDriveScreen(ModalScreen):
    """
    This dialog windows handles the TUI equivalent of API's
    setup_google_drive(). This asks to
    confirm the central hostkey, and takes password to setup
    SSH key pair.

    This is the one instance in which it is not possible for
    the TUI to nearly wrap the API, because the logic flow is
    broken up requiring user input (accept hostkey and input password).
    """

    def __init__(self, interface: Interface) -> None:
        super(SetupGoogleDriveScreen, self).__init__()

        self.interface = interface
        self.stage = 0

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup setup Google Drive. "
                    "Press OK to proceed.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Horizontal(
                Button("OK", id="setup_google_drive_ok_button"),
                Button("Cancel", id="setup_google_drive_cancel_button"),
                id="messagebox_buttons_horizontal",
            ),
            id="setup_google_drive_screen_container",
        )

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.pressed) -> None:
        """
        When each stage is successfully progressed by clicking the "ok" button,
        `self.stage` is iterated by 1. For saving and excepting hostkey,
        if there is a problem (error or user declines) the 'OK' button
        is frozen so it is not possible to proceed. For accepting password
        input, multiple attempts are allowed.
        """
        if event.button.id == "setup_google_drive_cancel_button":
            self.dismiss()
