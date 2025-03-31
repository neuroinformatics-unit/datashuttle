from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.interface import Interface

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
        self.stage = 0
        self.setup_worker: Worker | None = None

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Static(
                    "Ready to setup Google Drive. " "Press OK to proceed",
                    id="gdrive_setup_messagebox_message",
                ),
                id="gdrive_setup_messagebox_message_container",
            ),
            # Input(),
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
            self.ask_user_for_browser()

        elif event.button.id == "setup_gdrive_yes_button":
            self.open_browser_and_setup_gdrive_connection()

        elif event.button.id == "setup_gdrive_no_button":
            self.prompt_user_for_config_token()

        elif event.button.id == "setup_gdrive_enter_button":
            self.setup_gdrive_connection_using_config_token()

    def ask_user_for_browser(self) -> None:
        message = (
            "Are you running Datashuttle on a machine "
            "that can open a web browser?"
        )
        self.query_one("#gdrive_setup_messagebox_message").update(message)

        yes_button = Button("Yes", id="setup_gdrive_yes_button")
        no_button = Button("No", id="setup_gdrive_no_button")

        self.query_one("#setup_gdrive_ok_button").remove()
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            yes_button, no_button, before="#setup_gdrive_cancel_button"
        )

        self.stage += 1

    def open_browser_and_setup_gdrive_connection(self) -> None:
        # TODO: ADD SOME SUCCESS, OUTPUT
        message = "Please authenticate through browser."
        self.query_one("#gdrive_setup_messagebox_message").update(message)

        self.query_one("#setup_gdrive_yes_button").remove()
        self.query_one("#setup_gdrive_no_button").remove()

        async def _setup_gdrive_and_update_ui():
            worker = self.setup_gdrive_connection()
            self.setup_worker = worker
            if worker.is_running:
                await worker.wait()

            # TODO : check if successful
            self.show_finish_screen()

        asyncio.create_task(_setup_gdrive_and_update_ui())

    def prompt_user_for_config_token(self) -> None:

        self.query_one("#setup_gdrive_yes_button").remove()
        self.query_one("#setup_gdrive_no_button").remove()

        success, message = (
            self.interface.get_rclone_message_for_gdrive_without_browser()
        )

        if not success:
            self.display_failed()
            return

        self.query_one("#gdrive_setup_messagebox_message").update(
            message + "\nPress shift+click to copy."
        )

        enter_button = Button("Enter", id="setup_gdrive_enter_button")
        input_box = Input(id="setup_gdrive_config_token_input")

        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            enter_button, before="#setup_gdrive_cancel_button"
        )
        self.query_one("#setup_gdrive_screen_container").mount(
            input_box, before="#setup_gdrive_buttons_horizontal"
        )

    def setup_gdrive_connection_using_config_token(self) -> None:

        self.query_one("#setup_gdrive_config_token_input").disabled = True

        enter_button = self.query_one("#setup_gdrive_enter_button")
        enter_button.disabled = True

        config_token = self.query_one("#setup_gdrive_config_token_input").value

        async def _setup_gdrive_and_update_ui():
            worker = self.setup_gdrive_connection(config_token)
            self.setup_worker = worker
            if worker.is_running:
                await worker.wait()

            enter_button.remove()

            # TODO : check if successful
            self.show_finish_screen()

        asyncio.create_task(_setup_gdrive_and_update_ui())

    @work(exclusive=True, thread=True)
    def setup_gdrive_connection(
        self, config_token: Optional[str] = None
    ) -> Worker:
        self.interface.setup_google_drive_connection(config_token)
        self.stage += 1

    def show_finish_screen(self) -> None:
        message = "Setup Complete!"
        self.query_one("#setup_gdrive_cancel_button").remove()

        self.query_one("#gdrive_setup_messagebox_message").update(message)
        self.query_one("#setup_gdrive_buttons_horizontal").mount(
            Button("Finish", id="setup_gdrive_finish_button")
        )

    def display_failed(self) -> None:
        pass
