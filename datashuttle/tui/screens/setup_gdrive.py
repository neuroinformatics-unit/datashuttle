from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Static,
)

from datashuttle.tui.interface import Interface


class SetupGdriveScreen(ModalScreen):
    """
    This dialog window handles the TUI equivalent of API's setup_gdrive_connection().
    This guides the user through the interactive Google Drive setup process.

    This is different from SSH and AWS in that it requires
    the user to run a command in their terminal and complete
    the browser-based authentication flow.
    """

    def __init__(self, interface: Interface) -> None:
        super().__init__()
        self.interface = interface
        self.stage = 0

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup Google Drive connection. Press OK to proceed.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Horizontal(
                Button("OK", id="setup_gdrive_ok_button"),
                Button(
                    "Reset", id="setup_gdrive_reset_button", variant="warning"
                ),
                Button("Cancel", id="setup_gdrive_cancel_button"),
                id="messagebox_buttons_horizontal",
            ),
            id="setup_gdrive_screen_container",
        )

    def on_mount(self) -> None:
        # Hide the reset button initially
        self.query_one("#setup_gdrive_reset_button").visible = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        When each stage is successfully progressed by clicking the "ok" button,
        `self.stage` is iterated by 1. For Google Drive, we explain the process
        and provide the command to run interactively.
        """
        button_id = event.button.id

        if button_id == "setup_gdrive_cancel_button":
            self.dismiss(False)

        elif button_id == "setup_gdrive_reset_button":
            from datashuttle.utils import gdrive

            success, message = gdrive.reset_gdrive_config(
                self.interface.project.cfg
            )
            self.query_one("#messagebox_message_label").update(
                f"{message}\n\nPress OK to restart the setup process."
            )
            self.stage = 0
            self.query_one("#setup_gdrive_ok_button").label = "OK"
            self.query_one("#setup_gdrive_reset_button").visible = False

        elif button_id == "setup_gdrive_ok_button":
            if self.stage == 0:
                self.explain_gdrive_interactive_setup()
            elif self.stage == 1:
                self.show_gdrive_setup_command()
            elif self.stage == 2:
                self.verify_gdrive_connection()
            elif self.stage == 3:
                self.dismiss(True)

    def explain_gdrive_interactive_setup(self) -> None:
        """
        Explain to the user that Google Drive setup requires
        an interactive process in their terminal.
        """
        message = (
            "Setting up Google Drive requires an interactive authentication process.\n\n"
            "This involves:\n"
            "1. Running a command in your terminal\n"
            "2. Following prompts to open a web browser\n"
            "3. Authenticating and granting permissions to rclone\n\n"
            "Press OK to see the command to run."
        )

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def show_gdrive_setup_command(self) -> None:
        """
        Show the command the user needs to run in their terminal
        to complete the Google Drive setup.
        """
        success, output = self.interface.setup_rclone_gdrive_config()

        cfg = self.interface.get_configs()
        command = f"rclone config create {cfg.get_rclone_config_name()} drive root_folder_id {cfg['gdrive_folder_id']}"

        message = (
            "Run the following command in your terminal:\n\n"
            f"{command}\n\n"
            "Follow the interactive prompts to complete Google Drive setup.\n"
            "Once complete, click Verify to check your connection."
        )

        self.query_one("#messagebox_message_label").update(message)
        self.query_one("#setup_gdrive_ok_button").label = "Verify"
        self.query_one("#setup_gdrive_reset_button").visible = True
        self.stage += 1

    def verify_gdrive_connection(self) -> None:
        """
        Verify the Google Drive connection with better error reporting.
        """
        self.query_one("#messagebox_message_label").update(
            "Checking Google Drive connection...\n\n"
            "This may take a few seconds."
        )

        success, message = self.interface.verify_gdrive_connection()

        if success:
            self.query_one("#messagebox_message_label").update(
                f"Google Drive connection verified successfully!\n\n"
                f"{message}\n\n"
                f"Press Finish to complete the setup."
            )
            self.query_one("#setup_gdrive_ok_button").label = "Finish"
            self.query_one("#setup_gdrive_cancel_button").disabled = True
            self.stage += 1
        else:
            rclone_config_name = (
                self.interface.get_configs().get_rclone_config_name()
            )
            command = f"rclone config create {rclone_config_name} drive root_folder_id {self.interface.get_configs()['gdrive_folder_id']}"

            self.query_one("#messagebox_message_label").update(
                f"Google Drive connection verification failed:\n\n"
                f"{message}\n\n"
                f"Make sure you ran this exact command in your terminal:\n"
                f"{command}\n\n"
                f"And completed the authentication process.\n"
                f"Press Verify to try again, Reset to start over, or Cancel to exit."
            )
