from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Label, TabbedContent, TabPane

# from textual import events


class MyApp(App):
    TITLE = "DataShuttle"

    tui_path = Path(__file__).parents[1]
    CSS_PATH = tui_path / "css" / "tab_content.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        # yield Label("Do you love DataShuttle?", id = "question")
        with TabbedContent():
            with TabPane("Create", id="create"):
                yield Label("Create", id="create_text")
            with TabPane("Transfer", id="transfer"):
                yield Label("Transfer; Seems to work!")


if __name__ == "__main__":
    app = MyApp()
    app.run()
