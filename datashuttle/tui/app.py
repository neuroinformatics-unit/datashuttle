from pathlib import Path
from time import monotonic

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Checkbox,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from datashuttle import DataShuttle


class TypeBox(Static):
    """
    Dynamically-populated checkbox widget for convenient datatype
    selection during folder creation.

    Parameters
    ---------

    project_config: ConfigsClass
        Configuration dictionary from datashuttle (i.e. `project.cfg`).

    Attributes
    ----------

    type_out:
        List of datatypes (e.g. "behav" that will be passed to `make-folders`.)

    type_config:
        List of datatypes that were set as 'True' during datashuttle project setup
    """

    type_out = reactive("all")

    def __init__(self, project_cfg):
        super(TypeBox, self).__init__()

        self.type_config = [
            config.removeprefix("use_")
            for config, is_on in zip(project_cfg.keys(), project_cfg.values())
            if "use_" in config and is_on
        ]

    def compose(self):
        for type in self.type_config:
            yield Checkbox(type.title(), id=type, value=1)

    def on_checkbox_changed(self):
        """
        When a checkbox is clicked, update the `type_out` attribute
        with the datatypes to pass to `make_folders` datatype argument.
        """
        type_dict = {
            type: self.query_one(f"#{type}").value for type in self.type_config
        }
        self.type_out = [
            datatype
            for datatype, is_on in zip(type_dict.keys(), type_dict.values())
            if is_on
        ]


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

    # Change this to any local DataShuttle project for testing!
    project = DataShuttle("test_project")

    def compose(self) -> ComposeResult:
        """
        Composes widgets to the TUI in the order specified.
        """
        yield Header()
        with TabbedContent():
            with TabPane("Create", id="create"):
                yield DirectoryTree(
                    str(self.project.cfg.data["local_path"]), id="FileTree"
                )
                yield Label("Subject(s)", id="sub_label")
                yield Input(id="subject", placeholder="e.g. sub-001")
                yield Label("Session(s)")
                yield Input(id="session", placeholder="e.g. ses-001")
                yield Label("Datatype(s)")
                yield TypeBox(self.project.cfg)
                yield Button("Make Folders", id="make_folder")
                yield Input(
                    id="errors_on_create_page",
                    placeholder="Errors are printed here.",
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
            if event.path.stem.startswith("sub-"):
                self.query_one("#subject").value = str(event.path.stem)
            if event.path.stem.startswith("ses-"):
                self.query_one("#session").value = str(event.path.stem)
                self.query_one("#subject").value = str(event.path.parent.stem)
        self.prev_click_time = click_time

    def on_button_pressed(self, event: Button.Pressed):
        """
        Enables the Make Folder button to read out current input values
        and use these to call project.make_folders().
        """
        if event.button.id == "make_folder":
            sub_dir = self.query_one("#subject").value
            ses_dir = self.query_one("#session").value

            try:
                self.project.make_folders(
                    sub_names=sub_dir,
                    ses_names=ses_dir,
                    datatype=self.query_one("TypeBox").type_out,
                )
            except BaseException as e:
                self.query_one("#errors_on_create_page").value = str(e)

            self.query_one("#FileTree").reload()


if __name__ == "__main__":
    TuiApp().run()
