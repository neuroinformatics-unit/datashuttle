from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.interface import Interface
    from datashuttle.utils.custom_types import InterfaceOutput

from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Static,
)

from datashuttle.utils import rclone_encryption


class SetupGdriveScreen(ModalScreen):
    """Dialog window that sets up a Google Drive connection.

    If the config contains a "gdrive_client_id", the user is prompted
    to enter a client secret. If the user has access to a browser, a Google Drive
    authentication page will open. Otherwise, the user is asked to run a rclone command
    and input a config token.
    """

    def __init__(self, interface: Interface) -> None:
        """Initialise the SetupGdriveScreen."""
        super(SetupGdriveScreen, self).__init__()

        self.interface = interface
        self.no_browser_stage: None | str = "show_command_to_generate_code"
        self.setup_worker: Worker | None = None
        self.is_browser_available: bool = True
        self.gdrive_client_secret: Optional[str] = None

        # For handling credential inputs
        self.input_box: Input = Input(
            id="setup_gdrive_generic_input_box",
            placeholder="Enter value here",
        )
        self.enter_button = Button(
            "Enter", id="setup_gdrive_no_browser_enter_button"
        )

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

        1) `setup_gdrive_ok_button` : Starts the connection setup process.

        2) `setup_gdrive_has_browser_yes_button`  : A "yes" answer to the availability of browser question.
            On click, if "gdrive_client_id" is present in configs, the user is asked for client secret
            and proceeds to a browser authentication.

        3) `setup_gdrive_no_button`  : A "no" answer to the availability of browser question. On click,
            prompts the user to enter a config token by running an rclone command.

        4) `setup_gdrive_no_browser_enter_button` : To enter the client secret or config token.

        5) `setup_gdrive_set_encryption_yes_button` : To set a password on the RClone config file

        6) `setup_gdrive_set_encryption_no_button` : To skip setting a password on the RClone config file

        7) `setup_gdrive_finish_button` button : To finish the setup.

        8) "`setup_gdrive_cancel_button` : To cancel the setup at any step before completion.
        """
        if (
            event.button.id == "setup_gdrive_cancel_button"
            or event.button.id == "setup_gdrive_finish_button"
        ):
            # see setup_gdrive_connection_and_update_ui()
            if self.setup_worker and self.setup_worker.is_running:
                self.setup_worker.cancel()
                self.interface.terminate_gdrive_setup()
            self.dismiss()

        elif event.button.id == "setup_gdrive_ok_button":
            self.query_one("#setup_gdrive_ok_button").remove()

            if self.interface.project.cfg["gdrive_client_id"]:
                self.ask_user_for_gdrive_client_secret()
            else:
                self.ask_user_for_browser()

        elif event.button.id == "setup_gdrive_has_browser_yes_button":
            self.query_one("#setup_gdrive_has_browser_yes_button").remove()
            self.query_one("#setup_gdrive_no_button").remove()
            self.open_browser_and_setup_gdrive_connection(
                self.gdrive_client_secret
            )

        elif event.button.id == "setup_gdrive_no_button":
            self.is_browser_available = False
            self.query_one("#setup_gdrive_has_browser_yes_button").remove()
            self.query_one("#setup_gdrive_no_button").remove()
            self.prompt_user_for_config_token()

        elif event.button.id == "setup_gdrive_no_browser_enter_button":
            if (
                self.interface.project.cfg["gdrive_client_id"]
                and self.no_browser_stage == "show_command_to_generate_code"
            ):
                self.gdrive_client_secret = (
                    self.input_box.value.strip()
                    if self.input_box.value.strip()
                    else None
                )
                self.no_browser_stage = "setup_with_code"
                self.ask_user_for_browser()
            else:
                config_token = (
                    self.input_box.value.strip()
                    if self.input_box.value.strip()
                    else None
                )
                self.setup_gdrive_connection_using_config_token(
                    self.gdrive_client_secret, config_token
                )

        elif event.button.id == "setup_gdrive_set_encryption_yes_button":
            self.set_rclone_encryption()

        elif event.button.id == "setup_gdrive_set_encryption_no_button":
            self.set_finish_page("Setup complete!")

    # Setup the connection (with or without browser)
    # ----------------------------------------------------------------------------------

    def ask_user_for_browser(self) -> None:
        """Ask the user if their machine has access to a browser."""
        message = (
            "Are you running datashuttle on a machine "
            "that can open a web browser?"
        )
        self.update_message_box_message(message)

        if self.enter_button.is_mounted:
            self.enter_button.remove()

        if self.input_box.is_mounted:
            self.input_box.visible = False

        # Mount the Yes and No buttons
        yes_button = Button("Yes", id="setup_gdrive_has_browser_yes_button")
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
        message = (
            "Please authenticate through your browser (it should open automatically).\n\n"
            "It may take a moment for the connection to register after you confirm in the browser.\n\n"
        )

        self.update_message_box_message(message)

        self._task = asyncio.create_task(
            self.setup_gdrive_connection_and_update_ui(
                gdrive_client_secret=gdrive_client_secret
            ),
            name="setup_gdrive_connection_with_browser_task",
        )

    def prompt_user_for_config_token(self) -> None:
        """Prompt the user for the rclone config token for Google Drive setup."""
        success, message = (
            self.interface.get_rclone_message_for_gdrive_without_browser(
                self.gdrive_client_secret
            )
        )

        if not success:
            self.display_failed(message)
            return

        self.update_message_box_message(
            message + "\nPress shift+click to copy."
        )

        self.enter_button = Button(
            "Enter", id="setup_gdrive_no_browser_enter_button"
        )
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            self.enter_button, before="#setup_gdrive_cancel_button"
        )
        self.mount_input_box_before_buttons()

    def setup_gdrive_connection_using_config_token(
        self, gdrive_client_secret: str | None, config_token: str | None
    ) -> None:
        """Set up the Google Drive connection using rclone config token."""
        message = "Setting up connection..."
        self.update_message_box_message(message)

        self._task = asyncio.create_task(
            self.setup_gdrive_connection_and_update_ui(
                gdrive_client_secret=gdrive_client_secret,
                config_token=config_token,
            ),
            name="setup_gdrive_connection_without_browser_task",
        )

    async def setup_gdrive_connection_and_update_ui(
        self,
        gdrive_client_secret: Optional[str] = None,
        config_token: Optional[str] = None,
    ) -> None:
        """Start the Google Drive connection setup in a separate thread.

        The setup is run in a worker thread to avoid blocking the UI so that
        the user can cancel the setup if needed. This function starts the worker
        thread for Google Drive setup, sets `self.setup_worker` to the worker and
        awaits the worker to finish. After completion, it displays a
        success / failure screen. The setup on the lower level is a bit complicated.
        The worker thread runs the `setup_gdrive_connection` method of the
        `Interface` class which spawns an rclone process to set up the connection.
        The rclone process object is stored in the `Interface` class to handle closing
        the process as the thread does not kill the process itself upon cancellation and
        the process is awaited ensure that the process finishes and any raised errors are caught.
        Therefore, the worker thread and the rclone process are separately cancelled
        when the user presses the cancel button. (see `on_button_pressed`)
        """
        self.input_box.disabled = True
        self.enter_button.disabled = True

        try:
            worker = self.setup_gdrive_connection(
                gdrive_client_secret, config_token
            )
            self.setup_worker = worker
            if worker.is_running:
                await worker.wait()

            success, output = worker.result
            if success:
                self.show_password_screen()
                # This function is called from different screens that
                # contain different widgets. Therefore, remove all possible
                # widgets that may / may not be present on the previous screen.
                self.show_encryption_screen()
                for id in [
                    "#setup_gdrive_cancel_button",
                    "#setup_gdrive_generic_input_box",
                    "#setup_gdrive_no_browser_enter_button",
                ]:
                    try:
                        widget = self.query_one(id)
                        await widget.remove()
                    except NoMatches:
                        pass
            else:
                self.input_box.disabled = False
                self.enter_button.disabled = False
                self.display_failed(output)

        except Exception as exc:
            tb = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            self.display_failed(tb)

    @work(exclusive=True, thread=True)
    def setup_gdrive_connection(
        self,
        gdrive_client_secret: Optional[str] = None,
        config_token: Optional[str] = None,
    ) -> Worker[InterfaceOutput]:
        """Authenticate the Google Drive connection.

        This function runs in a worker thread to set up Google Drive connection.
        If the user had access to a browser, the underlying rclone commands called
        by this function are responsible for opening google's auth page to authenticate
        with Google Drive.
        """
        success, output = self.interface.setup_gdrive_connection(
            gdrive_client_secret, config_token
        )
        return success, output

    # Set encryption on RClone config
    # ----------------------------------------------------------------------------------

    def show_encryption_screen(self):
        """Show the screen asking the user whether to encrypt the Rclone password."""
        message = f"{rclone_encryption.get_explanation_message(self.interface.project.cfg)}"
        self.update_message_box_message(message)

        yes_button = Button("Yes", id="setup_gdrive_set_encryption_yes_button")
        no_button = Button("No", id="setup_gdrive_set_encryption_no_button")

        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            yes_button, no_button
        )

    def set_rclone_encryption(self):
        """Try and encrypt the Rclone config file and inform the user of success / failure."""
        success, output = self.interface.try_setup_rclone_encryption()

        if success:
            self.set_finish_page(
                "The encryption was successful. Setup complete!"
            )
        else:
            message = f"The password set up failed. Exception: {output}"
            self.update_message_box_message(message)

    def set_finish_page(self, message) -> None:
        """Show the final screen after successful set up."""
        self.query_one("#setup_gdrive_set_encryption_yes_button").remove()
        self.query_one("#setup_gdrive_set_encryption_no_button").remove()

        self.update_message_box_message(message)
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            Button("Finish", id="setup_gdrive_finish_button")
        )

    # UI Update Methods
    # ----------------------------------------------------------------------------------

    def display_failed(self, output) -> None:
        """Update the message box indicating the set-up failed."""
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
        self.input_box.visible = True
        self.input_box.value = ""
