from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import paramiko
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Static,
)


class SetupSshScreen(ModalScreen):
    """Dialog window that sets up an SSH connection.

    This asks to confirm the central hostkey, and takes password to setup
    SSH key pair. Under the hood uses `project.setup_ssh_connection()`.

    This is the one instance in which it is not possible for
    the TUI to nearly wrap the API, because the logic flow is
    broken up requiring user input (accept hostkey and input password).
    """

    def __init__(self, interface: Interface) -> None:
        """Initialise the SetupSshScreen."""
        super(SetupSshScreen, self).__init__()

        self.interface = interface
        self.stage = 0
        self.failed_password_attempts = 1

        self.key: paramiko.RSAKey

    def compose(self) -> ComposeResult:
        """Add widgets to the SetupSshScreen."""
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup SSH. Press OK to proceed.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Input(password=True, id="setup_ssh_password_input"),
            Horizontal(
                Button("OK", id="setup_ssh_ok_button"),
                Button("Cancel", id="setup_ssh_cancel_button"),
                id="messagebox_buttons_horizontal",
            ),
            id="setup_ssh_screen_container",
        )

    def on_mount(self) -> None:
        """Update widgets immediately after they are mounted."""
        self.query_one("#setup_ssh_password_input").visible = False

    def on_button_pressed(self, event: Button.pressed) -> None:
        """Handle button press on the SetupSshScreen.

        When each stage is successfully progressed by clicking the "ok" button,
        `self.stage` is iterated by 1. For saving and excepting hostkey,
        if there is a problem (error or user declines) the 'OK' button
        is frozen so it is not possible to proceed. For accepting password
        input, multiple attempts are allowed.
        """
        if event.button.id == "setup_ssh_cancel_button":
            self.dismiss()

        if event.button.id == "setup_ssh_ok_button":
            if self.stage == 0:
                self.ask_user_to_accept_hostkeys()

            elif self.stage == 1:
                self.save_hostkeys_and_prompt_password_input()

            elif self.stage == 2:
                self.use_password_to_setup_ssh_key_pairs()

            elif self.stage == 3:
                self.dismiss()

    def ask_user_to_accept_hostkeys(self) -> None:
        """Ask the user to accept the hostkey that identifies the central server.

        Get this hostkey and present it to user, clicking 'OK' is
        they are happy. If there is an error, block process (because it
        most likely is necessary to edit the central host id) and
        show the traceback.
        """
        success, output = self.interface.get_ssh_hostkey()

        if success:
            self.key = output

            message = (
                f"The host key is not cached for this server: "
                f"{self.interface.get_configs()['central_host_id']}.\nYou have no guarantee "
                f"that the server is the computer you think it is.\n"
                f"The server's {self.key.get_name()} key fingerprint is:\n\n "
                f"{self.key.get_base64()}\n\nIf you trust this host, to connect"
                f" and cache the host key, press OK: "
            )
        else:
            message = (
                "Could not connect to server. \nCheck the connection "
                f"and the central host ID : \n\n"
                f"{self.interface.get_configs()['central_host_id']} \n\n Traceback: {output}"
            )
            self.query_one("#setup_ssh_ok_button").disabled = True

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def save_hostkeys_and_prompt_password_input(self) -> None:
        """Get the user password for the central server.

        When 'OK' is pressed we go straight to
        'use_password_to_setup_ssh_key_pairs'.
        """
        success, output = self.interface.save_hostkey_locally(self.key)

        if success:
            message = (
                "Hostkey accepted. \n\nNext, input your password to the server "
                "below to setup an SSH key pair. You will not need to enter "
                "your password again. Press OK to confirm"
            )
            self.query_one("#setup_ssh_password_input").visible = True
        else:
            message = (
                f"Could not store host key. Check permissions "
                f"to: \n\n {self.interface.get_configs().hostkeys_path}.\n\n Traceback: {output}"
            )
            self.query_one("#setup_ssh_ok_button").disabled = True

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def use_password_to_setup_ssh_key_pairs(self) -> None:
        """Get the user password for the central server.

        If correct, SSH key pair is set up and 'OK' button changed
        to 'Finish'. Otherwise, continue allowing failed password attempts.
        """
        password = self.query_one("#setup_ssh_password_input").value

        success, output = self.interface.setup_key_pair_and_rclone_config(
            password
        )

        if success:
            message = (
                f"Connection successful! SSH key "
                f"saved to {self.interface.get_configs().ssh_key_path}"
            )
            self.query_one("#setup_ssh_ok_button").label = "Finish"
            self.query_one("#setup_ssh_cancel_button").disabled = True
            self.stage += 1

        else:
            message = (
                f"Password setup failed. Check password is correct and try again."
                f"\n\n{self.failed_password_attempts} failed password attempts."
                f"\n\n Traceback: {output}"
            )
            self.failed_password_attempts += 1

        self.query_one("#messagebox_message_label").update(message)
