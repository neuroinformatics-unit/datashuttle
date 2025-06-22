from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult


from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Static,
)

from datashuttle.configs import links


class GetHelpScreen(ModalScreen):
    """A screen with helpful information."""

    def __init__(self) -> None:
        """Initialise the GetHelpScreen."""
        super(GetHelpScreen, self).__init__()

        self.text = """
            For help getting started, check out the [@click=screen.link_docs()]Documentation[/],
            or ask at our [@click=screen.link_zulip()]Zulip Chat[/].

            For more information on specific interface features,
            hover the mouse over the element to see the 'tooltip'.

            Free to raise an issue anytime with questions, comments, feedback or
            bug reports on our [@click=screen.link_github_issues()]Issues[/] page.
        """

    def action_link_docs(self) -> None:
        """Link to datashuttle documentation."""
        webbrowser.open(links.get_docs_link())

    def action_link_github(self) -> None:
        """Link to datashuttle github."""
        webbrowser.open(links.get_github_link())

    def action_link_github_issues(self) -> None:
        """Link to datashuttle github issues."""
        webbrowser.open(links.get_link_github_issues())

    def action_link_zulip(self) -> None:
        """Link to datashuttle zulip."""
        webbrowser.open(links.get_link_zulip())

    def compose(self) -> ComposeResult:
        """Add widgets to the GetHelpScreen."""
        yield Container(
            Static(self.text, id="get_help_label"),
            Button("Main Menu", id="all_main_menu_buttons"),
            id="generic_screen_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on the GetHelpScreen."""
        if event.button.id == "all_main_menu_buttons":
            self.dismiss()
