from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Label, TabbedContent, TabPane


class TuiApp(App):
    """
    The main app page for the DataShuttle TUI.

    Running this application in a main block as below
    if __name__ == __main__:
         app = MyApp()
         app.run()

    Initialises the TUI event loop and starts the application.
    """

    TITLE = "DataShuttle"

    # Set path to TCSS
    tui_path = Path(__file__).parents[0]
    CSS_PATH = tui_path / "css" / "tab_content.tcss"

    # Set key-bindings
    BINDINGS = [
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    # Compose window
    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Create", id="create"):
                yield Label("Create", id="create_text")
            with TabPane("Transfer", id="transfer"):
                yield Label("Transfer; Seems to work!")
        yield Footer()


if __name__ == "__main__":
    app = TuiApp()
    app.run()
