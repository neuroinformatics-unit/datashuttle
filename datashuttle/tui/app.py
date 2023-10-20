from pathlib import Path
from time import monotonic

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import (
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    TabbedContent,
    TabPane,
)


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

    tui_path = Path(__file__).parent
    CSS_PATH = tui_path / "css" / "tab_content.tcss"

    BINDINGS = [
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    prev_click_time = 0.0

    def compose(self) -> ComposeResult:
        """
        Composes widgets to the TUI in the order specified.
        """

        yield Header()
        with TabbedContent():
            with TabPane("Create", id="create"):
                yield DirectoryTree(str(Path().home()), id="FileTree")
                yield Label("Folder Name")
                yield Input(
                    placeholder="Double-click on any folder to fill this field.",
                    id="subject",
                )
            with TabPane("Transfer", id="transfer"):
                yield Label("Transfer; Seems to work!")
        yield Footer()

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        After double-clicking a directory within the directory-tree
        widget, replaces contents of the \'Subject\' input widget
        with directory name. Double-click time is set to the
        Windows default (500 ms).
        """

        click_time = monotonic()
        if click_time - self.prev_click_time < 0.5:
            self.query_one("#subject").value = str(event.path)
        self.prev_click_time = click_time


if __name__ == "__main__":
    TuiApp().run()
