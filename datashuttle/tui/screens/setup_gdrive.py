from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.interface import Interface
    from datashuttle.utils.custom_types import InterfaceOutput

from textual import work
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Static,
)


class SetupGdriveScreen(ModalScreen):
    """ """

    def __init__(self, interface: Interface) -> None:
        super(SetupGdriveScreen, self).__init__()

        self.interface = interface
        self.stage: float = 0
        self.setup_worker: Worker | None = None
        self.gdrive_client_secret: Optional[str] = None

        self.input_box: Input = Input(
            id="setup_gdrive_generic_input_box",
            placeholder="Enter value here",
        )

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup Google Drive. " "Press OK to proceed",
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
        """ """
        if (
            event.button.id == "setup_gdrive_cancel_button"
            or event.button.id == "setup_gdrive_finish_button"
        ):
            if self.setup_worker and self.setup_worker.is_running:
                self.setup_worker.cancel()  # fix
            self.dismiss()

        elif event.button.id == "setup_gdrive_ok_button":
            if self.stage == 0:
                if self.interface.project.cfg["gdrive_client_id"]:
                    self.ask_user_for_gdrive_client_secret()
                else:
                    self.ask_user_for_browser()

            elif self.stage == 0.5:
                self.gdrive_client_secret = (
                    self.input_box.value.strip()
                    if self.input_box.value.strip()
                    else None
                )
                self.ask_user_for_browser()

        elif event.button.id == "setup_gdrive_yes_button":
            self.open_browser_and_setup_gdrive_connection()

        elif event.button.id == "setup_gdrive_no_button":
            self.prompt_user_for_config_token()

        elif event.button.id == "setup_gdrive_enter_button":
            self.setup_gdrive_connection_using_config_token()

    def ask_user_for_gdrive_client_secret(self) -> None:
        message = (
            "Please provide the client secret for Google Drive. "
            "You can find it in your Google Cloud Console."
        )
        self.update_message_box_message(message)

        ok_button = self.query_one("#setup_gdrive_ok_button")
        ok_button.label = "Enter"

        self.mount_input_box_before_buttons()

        self.stage += 0.5

    def ask_user_for_browser(self) -> None:
        message = (
            "Are you running Datashuttle on a machine "
            "that can open a web browser?"
        )
        self.update_message_box_message(message)

        self.query_one("#setup_gdrive_ok_button").remove()

        # Remove the input box if it was mounted previously
        if self.input_box.is_mounted:
            self.input_box.remove()

        # Mount the Yes and No buttons
        yes_button = Button("Yes", id="setup_gdrive_yes_button")
        no_button = Button("No", id="setup_gdrive_no_button")

        # Mount a cancel button
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            yes_button, no_button, before="#setup_gdrive_cancel_button"
        )

        self.stage += 0.5 if self.stage == 0.5 else 1

    def open_browser_and_setup_gdrive_connection(self) -> None:
        message = "Please authenticate through browser."
        self.update_message_box_message(message)

        # Remove the Yes and No buttons
        self.query_one("#setup_gdrive_yes_button").remove()
        self.query_one("#setup_gdrive_no_button").remove()

        asyncio.create_task(self.setup_gdrive_connection_and_update_ui())

    def prompt_user_for_config_token(self) -> None:

        self.query_one("#setup_gdrive_yes_button").remove()
        self.query_one("#setup_gdrive_no_button").remove()

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

        enter_button = Button("Enter", id="setup_gdrive_enter_button")
        self.input_box.value = ""

        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            enter_button, before="#setup_gdrive_cancel_button"
        )
        self.mount_input_box_before_buttons()

    def setup_gdrive_connection_using_config_token(self) -> None:

        self.input_box.disabled = True

        enter_button = self.query_one("#setup_gdrive_enter_button")
        enter_button.disabled = True

        config_token = self.input_box.value.strip()

        asyncio.create_task(
            self.setup_gdrive_connection_and_update_ui(config_token)
        )

    async def setup_gdrive_connection_and_update_ui(
        self, config_token: Optional[str] = None
    ) -> None:
        worker = self.setup_gdrive_connection(config_token)
        self.setup_worker = worker
        if worker.is_running:
            await worker.wait()

        if config_token:
            enter_button = self.query_one("#setup_gdrive_enter_button")
            enter_button.disabled = True

        success, output = worker.result
        if success:
            self.show_finish_screen()
        else:
            self.display_failed(output)

    @work(exclusive=True, thread=True)
    def setup_gdrive_connection(
        self, config_token: Optional[str] = None
    ) -> Worker[InterfaceOutput]:
        success, output = self.interface.setup_google_drive_connection(
            self.gdrive_client_secret, config_token
        )
        return success, output

    # ----------------------------------------------------------------------------------
    # UI Update Methods
    # ----------------------------------------------------------------------------------

    def show_finish_screen(self) -> None:
        message = "Setup Complete!"
        self.query_one("#setup_gdrive_cancel_button").remove()

        self.update_message_box_message(message)
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            Button("Finish", id="setup_gdrive_finish_button")
        )

    def display_failed(self, output) -> None:
        message = (
            f"Google Drive setup failed. Please check your configs and client secret"
            f"\n\n Traceback: {output}"
        )
        self.update_message_box_message(message)

    def update_message_box_message(self, message: str) -> None:
        self.query_one("#gdrive_setup_messagebox_message").update(message)

    def mount_input_box_before_buttons(self) -> None:
        self.query_one("#setup_gdrive_screen_container").mount(
            self.input_box, before="#setup_gdrive_buttons_horizontal"
        )
