from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Static,
)


class SetupGdriveScreen(ModalScreen):
    """
    This dialog window handles the TUI equivalent of API's
    setup_gdrive_connection(). This asks to confirm Google Drive
    credentials and takes an OAuth folder_id for setup.

    the TUI cannot simply wrap the API because
    the logic flow requires user input (OAuth folder_id and confirmation).
    """

    def __init__(self, interface: Interface) -> None:
        super(SetupGdriveScreen, self).__init__()

        self.interface = interface
        self.stage = 0
        self.folder_id: str = ""

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup Google Drive. Enter folder ID, then press OK.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Input(
                placeholder="Google Drive Folder ID",
                id="setup_gdrive_folder_input",
            ),
            Horizontal(
                Button("OK", id="setup_gdrive_ok_button"),
                Button("Cancel", id="setup_gdrive_cancel_button"),
                id="messagebox_buttons_horizontal",
            ),
            id="setup_gdrive_screen_container",
        )

    def on_mount(self) -> None:
        """Ensure UI is clean on start."""
        self.query_one("#setup_gdrive_folder_input").visible = False

    def on_button_pressed(self, event: Button.pressed) -> None:
        """
        Handle button presses for each stage:
        1. Confirm Google Drive credentials.
        2. Save credentials and prompt for OAuth folder_id.
        3. Use the folder_id to finalize Google Drive setup.
        """
        if event.button.id == "setup_gdrive_cancel_button":
            self.dismiss()

        if event.button.id == "setup_gdrive_ok_button":
            if self.stage == 0:
                self.ask_user_to_accept_gdrive_folder()

            elif self.stage == 1:
                self.save_gdrive_folder_and_prompt_setup()

            elif self.stage == 2:
                self.use_folder_id_to_setup_gdrive_connection()

            elif self.stage == 3:
                self.dismiss()

    def ask_user_to_accept_gdrive_folder(self) -> None:
        """
        Verify that the Google Drive folder ID is accessible.
        Ask the user to confirm trusting this folder for future use.
        """
        success, output = self.interface.get_gdrive_hostkey()

        if success:
            self.folder_id = output

            message = (
                f"The Google Drive folder ID '{self.folder_id}' is accessible.\n\n"
                "If you trust this folder and want to use it for transfers, press OK."
            )
        else:
            message = (
                "Could not verify the Google Drive folder.\nCheck the connection and the folder ID.\n\n"
                f"Traceback: {output}"
            )
            self.query_one("#setup_gdrive_ok_button").disabled = True

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def save_gdrive_folder_and_prompt_setup(self) -> None:
        """
        Once the Google Drive folder ID is accepted, confirm setup.
        No additional credentials are needed after this step.
        """
        success, output = self.interface.save_gdrive_key_locally(
            self.folder_id
        )

        if success:
            message = (
                "Google Drive folder ID verified.\n\nSetup is now complete. "
                "You can proceed to transfer files."
            )
        else:
            message = (
                f"Could not store Google Drive folder ID. Check permissions "
                f"for: \n\n {self.interface.get_configs().gdrive_key_path}.\n\n Traceback: {output}"
            )
            self.query_one("#setup_gdrive_ok_button").disabled = True

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def use_folder_id_to_setup_gdrive_connection(self) -> None:
        """
        Use the OAuth folder_id to complete the Google Drive setup.
        If successful, the OK button changes to 'Finish'.
        Otherwise, prompt for another attempt.
        """
        folder_id = self.query_one("#setup_gdrive_folder_id_input").value

        success, output = self.interface.setup_gdrive_folder_and_rclone_config(
            folder_id
        )

        if success:
            message = (
                f"Google Drive setup successful! Credentials saved to "
                f"{self.interface.get_configs().gdrive_credentials_path}"
            )
            self.query_one("#setup_gdrive_ok_button").label = "Finish"
            self.query_one("#setup_gdrive_cancel_button").disabled = True
            self.stage += 1

        else:
            message = (
                "Google Drive setup failed. Check that your OAuth folder_id is correct and try again."
                f"\n\n{self.failed_attempts} failed attempts."
                f"\n\n Traceback: {output}"
            )
            self.failed_attempts += 1

        self.query_one("#messagebox_message_label").update(message)
