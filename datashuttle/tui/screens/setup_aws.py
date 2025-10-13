from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface

from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from datashuttle.utils import rclone_encryption


class SetupAwsScreen(ModalScreen):
    """Dialog window that sets up connection to an Amazon Web Service S3 bucket.

    This asks the user for confirmation to proceed with the setup,
    and then prompts the user for the AWS Secret Access Key.

    The secret access key is then used to set up rclone config for AWS S3.
    """

    def __init__(self, interface: Interface) -> None:
        """Initialise the SetupAwsScreen."""
        super(SetupAwsScreen, self).__init__()

        self.interface = interface
        self.stage = "init"

    def compose(self) -> ComposeResult:
        """Set widgets on the SetupAwsScreen."""
        yield Container(
            Vertical(
                Static(
                    "Ready to setup AWS connection. Press OK to proceed",
                    id="setup_aws_messagebox_message",
                ),
                Input(password=True, id="setup_aws_secret_access_key_input"),
                id="setup_aws_messagebox_message_container",
            ),
            Horizontal(
                Button("OK", id="setup_aws_ok_button"),
                Button("Cancel", id="setup_aws_cancel_button"),
                id="setup_aws_buttons_horizontal",
            ),
            id="setup_aws_screen_container",
        )

    def on_mount(self) -> None:
        """Update widgets immediately after mounting."""
        self.query_one("#setup_aws_secret_access_key_input").visible = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press on the screen.

        The `setup_aws_ok_button` is used for all 'positive' events ('Yes, Ok')
        and 'setup_aws_cancel_button' is used for 'negative' events ('No', 'Cancel').
        The appropriate action to take on the button press is determined by the
        current stage.

        """
        if event.button.id == "setup_aws_cancel_button":
            if self.stage == "ask_rclone_encryption":
                message = "AWS Connection Successful!"  #
                self.query_one("#setup_aws_messagebox_message").update(message)
                self.query_one("#setup_aws_ok_button").label = "Finish"
                self.query_one("#setup_aws_cancel_button").remove()
                self.stage = "finished"
            else:
                self.dismiss()

        elif event.button.id == "setup_aws_ok_button":
            if self.stage == "init":
                self.prompt_user_for_aws_secret_access_key()

            elif self.stage == "use_secret_access_key":
                self.use_secret_access_key_to_setup_aws_connection()

            elif self.stage == "ask_rclone_encryption":
                self.set_rclone_encryption()

            elif self.stage == "finished":
                self.dismiss()

    def prompt_user_for_aws_secret_access_key(self) -> None:
        """Set widgets for user to input AWS key."""
        message = "Please Enter your AWS Secret Access Key"

        self.query_one("#setup_aws_messagebox_message").update(message)
        self.query_one("#setup_aws_secret_access_key_input").visible = True

        self.query_one("#setup_aws_ok_button")

        self.stage = "use_secret_access_key"

    def use_secret_access_key_to_setup_aws_connection(self) -> None:
        """Set up the AWS connection and failure. If success, move onto the
        rclone_encryption screen.

        """
        secret_access_key = self.query_one(
            "#setup_aws_secret_access_key_input"
        ).value

        success, output = self.interface.setup_aws_connection(
            secret_access_key
        )

        if success:
            message = f"{rclone_encryption.get_explanation_message(self.cfg)}"
            self.query_one("#setup_aws_messagebox_message").update(message)

            self.query_one("#setup_aws_secret_access_key_input").remove()
            self.query_one("#setup_aws_ok_button").label = "Yes"
            self.query_one("#setup_aws_cancel_button").label = "No"
            self.stage = "ask_rclone_encryption"
        else:
            message = (
                f"AWS setup failed. Please check your configs and secret access key"
                f"\n\n Traceback: {output}"
            )
            self.query_one(
                "#setup_aws_secret_access_key_input"
            ).disabled = True

            self.query_one("#setup_aws_ok_button").label = "Retry"
            self.query_one("#setup_aws_messagebox_message").update(message)

    def set_rclone_encryption(self):
        """"""
        success, output = self.interface.try_setup_rclone_encryption()

        if success:
            message = (
                "The rclone_encryption was successfully set. Setup complete!"
            )
            self.query_one("#setup_aws_messagebox_message").update(message)
            self.query_one("#setup_aws_ok_button").label = "Finish"
            self.query_one("#setup_aws_cancel_button").remove()
            self.stage = "finished"
        else:
            message = (
                f"The rclone_encryption set up failed. Exception: {output}"
            )
            self.query_one("#setup_aws_messagebox_message").update(message)
