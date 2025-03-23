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


class SetupAwsScreen(ModalScreen):
    """
    This dialog window handles the TUI equivalent of API's
    setup_aws_connection(). This asks to confirm AWS credentials
    and takes an access key for setup.

    the TUI cannot simply wrap the API because
    the logic flow requires user input (AWS credentials and key).
    """

    def __init__(self, interface: Interface) -> None:
        super(SetupAwsScreen, self).__init__()

        self.interface = interface
        self.stage = 0
        self.bucket_name: str = ""
        self.aws_region: str = ""
        self.failed_attempts = 1

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup AWS S3. Enter bucket name and region, then press OK.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Input(placeholder="AWS Bucket Name", id="setup_aws_bucket_input"),
            Input(placeholder="AWS Region", id="setup_aws_region_input"),
            Horizontal(
                Button("OK", id="setup_aws_ok_button"),
                Button("Cancel", id="setup_aws_cancel_button"),
                id="messagebox_buttons_horizontal",
            ),
            id="setup_aws_screen_container",
        )

    def on_mount(self) -> None:
        """Hide region input until the bucket name is verified."""
        self.query_one("#setup_aws_bucket_input").visible = False
        self.query_one("#setup_aws_region_input").visible = False

    def on_button_pressed(self, event: Button.pressed) -> None:
        """
        Handle button presses for each stage:
        1. Confirm AWS credentials.
        2. Save credentials and prompt for key.
        3. Use the key to finalize AWS setup.
        """
        if event.button.id == "setup_aws_cancel_button":
            self.dismiss()

        if event.button.id == "setup_aws_ok_button":
            if self.stage == 0:
                self.ask_user_to_accept_aws_bucket()

            elif self.stage == 1:
                self.save_aws_bucket_and_prompt_region_input()

            elif self.stage == 2:
                self.use_aws_bucket_and_region_to_setup_aws_connection()

            elif self.stage == 3:
                self.dismiss()

    def ask_user_to_accept_aws_bucket(self) -> None:
        """
        Verify that the AWS S3 bucket is accessible.
        Ask the user to confirm trusting this bucket for future use.
        """
        success, output = self.interface.get_aws_hostkey()

        if success:
            self.bucket_name = output

            message = (
                f"The AWS bucket '{self.bucket_name}' is accessible.\n\n"
                "If you trust this bucket and want to use it for transfers, press OK."
            )
        else:
            message = (
                "Could not verify the AWS bucket.\nCheck the connection and the bucket name.\n\n"
                f"Traceback: {output}"
            )
            self.query_one("#setup_aws_ok_button").disabled = True

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def save_aws_bucket_and_prompt_region_input(self) -> None:
        """
        Once the AWS bucket is accepted, prompt the user for the region.
        When 'OK' is pressed, we go straight to 'use_region_to_setup_aws_connection'.
        """
        success, output = self.interface.save_aws_key_locally(self.bucket_name)

        if success:
            message = (
                "AWS bucket verified.\n\nNext, enter your AWS region below to complete setup. "
                "Press OK to confirm."
            )
            self.query_one("#setup_aws_region_input").visible = True
        else:
            message = (
                f"Could not store AWS bucket name. Check permissions "
                f"for: \n\n {self.interface.get_configs().aws_key_path}.\n\n Traceback: {output}"
            )
            self.query_one("#setup_aws_ok_button").disabled = True

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def use_aws_bucket_and_region_to_setup_aws_connection(self) -> None:
        """
        Use the AWS bucket name and region to complete the setup.
        If successful, the OK button changes to 'Finish'.
        Otherwise, prompt for another attempt.
        """
        bucket_name = self.query_one("#setup_aws_bucket_name_input").value
        region = self.query_one("#setup_aws_region_input").value

        success, output = self.interface.setup_aws_bucket_and_rclone_config(
            bucket_name, region
        )

        if success:
            message = (
                f"AWS setup successful! Config saved to "
                f"{self.interface.get_configs().aws_credentials_path}"
            )
            self.query_one("#setup_aws_ok_button").label = "Finish"
            self.query_one("#setup_aws_cancel_button").disabled = True
            self.stage += 1

        else:
            message = (
                "AWS setup failed. Check that your bucket name and region are correct and try again."
                f"\n\n{self.failed_attempts} failed attempts."
                f"\n\nTraceback: {output}"
            )
            self.failed_attempts += 1

        self.query_one("#messagebox_message_label").update(message)
