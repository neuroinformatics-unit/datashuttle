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

from datashuttle.utils import rclone_encryption


class SetupSshScreen(ModalScreen):
    """Dialog window that sets up an SSH connection.

    This asks to confirm the central hostkey, and takes password to set up
    SSH key pair as well as encrypting the RClone config.

    Due to how textual works, it is simpler for each button press to
    trigger an action (e.g. set up host key) and then set up the widgets
    for the next screen. Then, when the next button is pressed, we can
    continue in this way of managing the screens.
    """

    def __init__(self, interface: Interface) -> None:
        """Initialise the SetupSshScreen."""
        super(SetupSshScreen, self).__init__()

        self.interface = interface
        self.stage = "init"
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
            if self.stage == "set_up_encryption":
                self.show_connection_successful_message()
            else:
                self.dismiss(False)

        if event.button.id == "setup_ssh_ok_button":
            if self.stage == "init":
                self.ask_user_to_accept_hostkeys()

            elif self.stage == "save_hostkeys":
                self.save_hostkeys_and_prompt_password_input()

            elif self.stage == "setup_and_ask_for_encryption":
                self.use_password_to_setup_ssh_key_pairs()

            elif self.stage == "set_up_encryption":
                self.try_setup_rclone_encryption()

            elif self.stage == "show_success_message":
                self.show_connection_successful_message()

            elif self.stage == "finished":
                self.dismiss(True)

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
        self.stage = "save_hostkeys"

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
        self.stage = "setup_and_ask_for_encryption"

    def use_password_to_setup_ssh_key_pairs(self) -> None:
        """Set up the SSH key pair using the user-supplied password to the central server.

        Next, set up the request asking if they would like to set
        a (separate) password on their RClone config, using the
        system credential manager.
        """
        password = self.query_one("#setup_ssh_password_input").value

        success, output = self.interface.setup_key_pair_and_rclone_config(
            password
        )

        if success:
            message = (
                f"Connection set up successfully.\n"
                f"{rclone_encryption.get_explanation_message(self.cfg)}"
            )
            self.query_one("#setup_ssh_ok_button").label = "Yes"
            self.query_one("#setup_ssh_cancel_button").label = "No"
            self.query_one("#setup_ssh_password_input").visible = False
            self.stage = (
                "set_up_encryption"  # Go to rclone encryption set up screen
            )

        else:
            message = (
                f"Password setup failed. Check password is correct and try again."
                f"\n\n{self.failed_password_attempts} failed password attempts."
                f"\n\n Traceback: {output}"
            )
            self.failed_password_attempts += 1

        self.query_one("#messagebox_message_label").update(message)

    def try_setup_rclone_encryption(self):
        """Try and encrypt the RClone config using the system credential manager.

        If successful, the next screen confirms success.
        """
        success, output = self.interface.try_setup_rclone_encryption()

        if success:
            message = "Rclone config file was successfully encrypted."
            self.query_one("#messagebox_message_label").update(message)
            self.query_one("#setup_ssh_ok_button").label = "Ok"
            self.query_one("#setup_ssh_cancel_button").remove()
        else:
            message = f"Encryption failed. Exception: {output}"
            self.query_one("#messagebox_message_label").update(message)

        self.stage = "show_success_message"

    def show_connection_successful_message(self):
        """Show the final screen indicating the connection was successfully set up."""
        self.query_one("#setup_ssh_ok_button").label = "Finish"

        # Depending on what was the previous screen, `setup_ssh_cancel_button`
        # may or may not be displayed.
        try:
            self.query_one("#setup_ssh_cancel_button").remove()
        except BaseException:
            pass

        message = "Connection was set up successfully. SSH key saved to the RClone config file."
        self.query_one("#messagebox_message_label").update(message)
        self.stage = "finished"
