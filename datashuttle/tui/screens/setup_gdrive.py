from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.interface import Interface
    from datashuttle.utils.custom_types import InterfaceOutput

from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Static,
)


class SetupGdriveScreen(ModalScreen):
    """Dialog window that sets up a Google Drive connection.

    If the config contains a "gdrive_client_id", the user is prompted
    to enter a client secret. If the user has access to a browser, a Google Drive
    authentication page will open. Otherwise, the user is asked to enter path to a
    service account file.
    """

    def __init__(self, interface: Interface) -> None:
        """Initialise the SetupGdriveScreen."""
        super(SetupGdriveScreen, self).__init__()

        self.interface = interface
        self.stage: int = 0
        self.setup_worker: Worker | None = None
        self.is_browser_available: bool = True

        # For handling credential inputs
        self.input_box: Input = Input(
            id="setup_gdrive_generic_input_box",
            placeholder="Enter value here",
        )
        self.enter_button = Button("Enter", id="setup_gdrive_enter_button")

    def compose(self) -> ComposeResult:
        """Add widgets to the SetupGdriveScreen."""
        yield Container(
            Vertical(
                Static(
                    "Ready to setup Google Drive. Press OK to proceed",
                    id="gdrive_setup_messagebox_message",
                ),
                id="gdrive_setup_messagebox_message_container",
            ),
            Horizontal(
                Button("OK", id="setup_gdrive_ok_button"),
                Button("Cancel", id="setup_gdrive_cancel_button"),
                id="setup_gdrive_buttons_horizontal",
            ),
            id="setup_gdrive_screen_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on the screen.

        This dialog window operates using 6 buttons:

        1) "ok" button : Starts the connection setup process.

        2) "yes" button : A "yes" answer to the availability of browser question. On click,
            if "gdrive_client_id" is present in configs, the user is asked for client secret
            and proceeds to a browser authentication.

        3) "no" button : A "no" answer to the availability of browser question. On click,
            prompts the user to enter path to their service account file.

        4) "enter" button : To enter the client secret or service account file path.

        5) "finish" button : To finish the setup.

        6) "cancel" button : To cancel the setup at any step before completion.
        """
        if (
            event.button.id == "setup_gdrive_cancel_button"
            or event.button.id == "setup_gdrive_finish_button"
        ):
            if self.setup_worker and self.setup_worker.is_running:
                self.setup_worker.cancel()  # fix
                self.interface.terminate_google_drive_setup()
            self.dismiss()

        elif event.button.id == "setup_gdrive_ok_button":
            self.ask_user_for_browser()

        elif event.button.id == "setup_gdrive_yes_button":
            self.remove_yes_no_buttons()

            if self.interface.project.cfg["gdrive_client_id"]:
                self.ask_user_for_gdrive_client_secret()
            else:
                self.open_browser_and_setup_gdrive_connection()

        elif event.button.id == "setup_gdrive_no_button":
            self.is_browser_available = False
            self.remove_yes_no_buttons()
            self.prompt_user_for_service_account_filepath()

        elif event.button.id == "setup_gdrive_enter_button":
            if self.is_browser_available:
                gdrive_client_secret = (
                    self.input_box.value.strip()
                    if self.input_box.value.strip()
                    else None
                )
                self.open_browser_and_setup_gdrive_connection(
                    gdrive_client_secret
                )
            else:
                service_account_filepath = (
                    self.input_box.value.strip()
                    if self.input_box.value.strip()
                    else None
                )
                self.setup_gdrive_connection_using_service_account(
                    service_account_filepath
                )

    def ask_user_for_browser(self) -> None:
        """Ask the user if their machine has access to a browser."""
        message = (
            "Are you running Datashuttle on a machine "
            "that can open a web browser?"
        )
        self.update_message_box_message(message)

        self.query_one("#setup_gdrive_ok_button").remove()

        # Mount the Yes and No buttons
        yes_button = Button("Yes", id="setup_gdrive_yes_button")
        no_button = Button("No", id="setup_gdrive_no_button")

        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            yes_button, no_button, before="#setup_gdrive_cancel_button"
        )

    def ask_user_for_gdrive_client_secret(self) -> None:
        """Ask the user for Google Drive client secret.

        Only called if the datashuttle config has a `gdrive_client_id`.
        """
        message = (
            "Please provide the client secret for Google Drive. "
            "You can find it in your Google Cloud Console."
        )
        self.update_message_box_message(message)

        self.query_one("#setup_gdrive_screen_container").mount(
            self.enter_button, before="#setup_gdrive_cancel_button"
        )

        self.mount_input_box_before_buttons(is_password=True)

    def open_browser_and_setup_gdrive_connection(
        self, gdrive_client_secret: Optional[str] = None
    ) -> None:
        """Set up Google Drive when the user has a browser.

        Starts an asyncio task to setup Google Drive
        connection and updates the UI with success/failure.

        The connection setup is asynchronous so that the user is able to
        cancel the setup if anything goes wrong without quitting datashuttle altogether.
        """
        message = "Please authenticate through browser."
        self.update_message_box_message(message)

        asyncio.create_task(
            self.setup_gdrive_connection_and_update_ui(
                gdrive_client_secret=gdrive_client_secret
            )
        )

    def prompt_user_for_service_account_filepath(self) -> None:
        """Set up widgets and prompt user for their service account file path for browser-less connection."""
        message = "Please enter your service account file path."

        self.update_message_box_message(message)

        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            self.enter_button, before="#setup_gdrive_cancel_button"
        )
        self.mount_input_box_before_buttons()

    def setup_gdrive_connection_using_service_account(
        self, service_account_filepath: Optional[str] = None
    ) -> None:
        """Set up the Google Drive connection using service account and show success message."""
        message = "Setting up connection."
        self.update_message_box_message(message)

        asyncio.create_task(
            self.setup_gdrive_connection_and_update_ui(
                service_account_filepath=service_account_filepath
            )
        )

    async def setup_gdrive_connection_and_update_ui(
        self,
        gdrive_client_secret: Optional[str] = None,
        service_account_filepath: Optional[str] = None,
    ) -> None:
        """Start the Google Drive connection setup in a separate thread.

        This requires asynchronous processing and awaits for its completion.
        After completion, it displays a success / failure screen.
        """
        self.input_box.disabled = True
        self.enter_button.disabled = True

        worker = self.setup_gdrive_connection(
            gdrive_client_secret, service_account_filepath
        )
        self.setup_worker = worker
        if worker.is_running:
            await worker.wait()

        success, output = worker.result
        if success:
            self.show_finish_screen()
        else:
            self.input_box.disabled = False
            self.enter_button.disabled = False
            self.display_failed(output)

    @work(exclusive=True, thread=True)
    def setup_gdrive_connection(
        self,
        gdrive_client_secret: Optional[str] = None,
        service_account_filepath: Optional[str] = None,
    ) -> Worker[InterfaceOutput]:
        """Authenticate the Google Drive connection.

        This function runs in a worker thread to set up Google Drive connection.
        If the user had access to a browser, the underlying rclone commands called
        by this function are responsible for opening google's auth page to authenticate
        with Google Drive.
        """
        success, output = self.interface.setup_google_drive_connection(
            gdrive_client_secret, service_account_filepath
        )
        return success, output

    # ----------------------------------------------------------------------------------
    # UI Update Methods
    # ----------------------------------------------------------------------------------

    def show_finish_screen(self) -> None:
        """Show the final screen after successful set up."""
        message = "Setup Complete!"
        self.query_one("#setup_gdrive_cancel_button").remove()

        self.update_message_box_message(message)
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            Button("Finish", id="setup_gdrive_finish_button")
        )

    def display_failed(self, output) -> None:
        """Update the message box indicating the set up failed."""
        message = (
            f"Google Drive setup failed. Please check your credentials"
            f"\n\n Traceback: {output}"
        )
        self.update_message_box_message(message)

    def update_message_box_message(self, message: str) -> None:
        """Update the text message displayed to the user."""
        self.query_one("#gdrive_setup_messagebox_message").update(message)

    def mount_input_box_before_buttons(
        self, is_password: bool = False
    ) -> None:
        """Add the Input box to the screen.

        This Input may be used for entering connection details or a password.
        """
        self.input_box.password = is_password
        self.input_box.styles.dock = "bottom"
        self.query_one("#gdrive_setup_messagebox_message_container").mount(
            self.input_box, after="#gdrive_setup_messagebox_message"
        )

    def remove_yes_no_buttons(self) -> None:
        """Remove yes and no buttons."""
        self.query_one("#setup_gdrive_yes_button").remove()
        self.query_one("#setup_gdrive_no_button").remove()
