from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface

from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


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
        self.stage = 0

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
        """Handle button press on the screen."""
        if event.button.id == "setup_aws_cancel_button":
            self.dismiss()

        if event.button.id == "setup_aws_ok_button":
            if self.stage == 0:
                self.prompt_user_for_aws_secret_access_key()

            elif self.stage == 1:
                self.use_secret_access_key_to_setup_aws_connection()

            elif self.stage == 2:
                self.dismiss()

    def prompt_user_for_aws_secret_access_key(self) -> None:
        """Set widgets for user to input AWS key."""
        message = "Please Enter your AWS Secret Access Key"

        self.query_one("#setup_aws_messagebox_message").update(message)
        self.query_one("#setup_aws_secret_access_key_input").visible = True

        self.stage += 1

    def use_secret_access_key_to_setup_aws_connection(self) -> None:
        """Set up the AWS connection and inform user of success or failure."""
        secret_access_key = self.query_one(
            "#setup_aws_secret_access_key_input"
        ).value

        try:
            success, output = self.interface.setup_aws_connection(
                secret_access_key
            )

            if success:
                message = "AWS Connection Successful!"
                self.query_one(
                    "#setup_aws_secret_access_key_input"
                ).visible = False

            else:
                message = (
                    f"AWS setup failed. Please check your configs and secret access key"
                    f"\n\n Traceback: {output}"
                )
                self.query_one(
                    "#setup_aws_secret_access_key_input"
                ).disabled = True

            self.query_one("#setup_aws_ok_button").label = "Finish"
            self.query_one("#setup_aws_messagebox_message").update(message)
            self.query_one("#setup_aws_cancel_button").disabled = True
            self.stage += 1
        finally:
            # Clear secret key from memory and input widget
            if secret_access_key:
                secret_access_key = None
                del secret_access_key
            # Clear the input widget value
            self.query_one("#setup_aws_secret_access_key_input").value = ""
