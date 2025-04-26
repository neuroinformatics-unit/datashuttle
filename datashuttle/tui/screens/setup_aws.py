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
    LoadingIndicator,
)

class SetupAwsScreen(ModalScreen):
    """
    This dialog window handles the TUI equivalent of API's setup_aws_connection().
    This guides the user through AWS credential setup, then tests the connection.

    Like the SSH setup, this requires user input and interaction
    since AWS credentials may need to be set up externally.
    """

    def __init__(self, interface: Interface) -> None:
        super().__init__()
        self.interface = interface
        self.stage = 0
        self.is_checking = False

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup AWS S3 connection. Press OK to proceed.",
                    id="messagebox_message_label",
                ),
                id="messagebox_message_container",
            ),
            Horizontal(
                Button("OK", id="setup_aws_ok_button"),
                Button("Reset", id="setup_aws_reset_button", variant="warning"),
                Button("Cancel", id="setup_aws_cancel_button"),
                id="messagebox_buttons_horizontal",
            ),
            id="setup_aws_screen_container",
        )

    def on_mount(self) -> None:
        # Hide the reset button initially
        self.query_one("#setup_aws_reset_button").visible = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events with improved verification logic.
        """
        button_id = event.button.id
        
        if self.is_checking and button_id != "setup_aws_cancel_button":
            return
                
        if button_id == "setup_aws_cancel_button":
            self.dismiss(False)
                
        elif button_id == "setup_aws_reset_button":
            from datashuttle.utils import aws
            success, message = aws.reset_aws_config(self.interface.project.cfg)
            self.query_one("#messagebox_message_label").update(
                f"{message}\n\nPress OK to restart the setup process."
            )
            self.stage = 0
            self.query_one("#setup_aws_ok_button").label = "OK"
            self.query_one("#setup_aws_reset_button").visible = False
                
        elif button_id == "setup_aws_ok_button":
            if self.stage == 0:
                self.explain_aws_credential_requirements()
            elif self.stage == 1:
                self.attempt_aws_rclone_config()
            elif self.stage == 2:
                self.verify_aws_connection()
            elif self.stage == 3:
                self.dismiss(True)


    def explain_aws_credential_requirements(self) -> None:
        """
        Explain to the user what AWS credentials are needed and
        how they should be configured before proceeding.
        """
        message = (
            "To use AWS S3 with datashuttle, you need AWS credentials configured.\n\n"
            "Ensure your AWS credentials are set up in one of these ways:\n"
            "1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)\n"
            "2. Shared credential file (~/.aws/credentials)\n"
            "3. AWS config file (~/.aws/config)\n"
            "4. IAM instance profile (if running on EC2)\n\n"
            "Press OK once your credentials are ready to create the Rclone configuration."
        )

        self.query_one("#messagebox_message_label").update(message)
        self.stage += 1

    def attempt_aws_rclone_config(self) -> None:
        """
        Attempt to create the rclone configuration for AWS.
        Update the message based on success or failure.
        """
        self.is_checking = True
        success, output = self.interface.setup_rclone_aws_config()
        self.is_checking = False

        if success:
            cfg = self.interface.get_configs()
            message = (
                f"Rclone configuration for AWS S3 created successfully.\n\n"
                f"Bucket: {cfg['aws_bucket_name']}\n"
                f"Region: {cfg['aws_region'] or 'Default'}\n\n"
                "Press OK to verify the connection."
            )
            self.query_one("#setup_aws_reset_button").visible = True
            self.stage += 1
        else:
            message = (
                f"Failed to create Rclone configuration for AWS.\n\n"
                f"Error details: {output}\n\n"
                "Check your AWS credentials and bucket configuration.\n"
                "Press OK to try again or Cancel to abort."
            )

        self.query_one("#messagebox_message_label").update(message)

    def verify_aws_connection(self) -> None:
        """
        Verify AWS connection with direct rclone check.
        """
        self.query_one("#messagebox_message_label").update(
            "Checking AWS S3 connection...\n\n"
            "This may take a few seconds."
        )
        
        self.is_checking = True
        
        cfg = self.interface.get_configs()
        rclone_config_name = cfg.get_rclone_config_name()
        bucket_name = cfg["aws_bucket_name"]
        
        from datashuttle.utils import rclone
        output = rclone.call_rclone(
            f"lsf {rclone_config_name}:{bucket_name} --max-depth 1",
            pipe_std=True
        )
        
        self.is_checking = False
        
        if output.returncode == 0:
            self.query_one("#messagebox_message_label").update(
                f"AWS S3 connection verified successfully!\n\n"
                f"Successfully connected to bucket: {bucket_name}\n\n"
                f"Press Finish to complete the setup."
            )
            self.query_one("#setup_aws_ok_button").label = "Finish"
            self.query_one("#setup_aws_cancel_button").disabled = True
            self.stage += 1
        else:
            error = output.stderr.decode("utf-8")
            self.query_one("#messagebox_message_label").update(
                f"AWS S3 connection verification failed:\n\n"
                f"Error accessing bucket '{bucket_name}':\n{error}\n\n"
                f"Check your AWS credentials and bucket configuration.\n"
                f"Press OK to try again, Reset to start over, or Cancel to abort."
            )
