from pathlib import Path
from time import monotonic

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Checkbox,
    DirectoryTree,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from datashuttle import DataShuttle
from datashuttle.utils.folders import get_existing_project_paths_and_names


class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    def __init__(self, message):
        super(QuitScreen, self).__init__()

        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Container(Static(self.message, id="real_label"), id="label_x"),
            Container(Button("OK"), id="button_x"),
            id="dialog",
        )

    def on_button_pressed(self) -> None:
        self.dismiss()


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


class TabScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.
    """

    TITLE = "DataShuttle"

    prev_click_time = 0.0

    def __init__(self, mainwindow, project):
        super(TabScreen, self).__init__()
        self.mainwindow = mainwindow
        self.project = project

    def compose(self) -> ComposeResult:
        """
        Composes widgets to the TUI in the order specified.
        """
        yield Header()
        yield Button("Main Menu", id="return")
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
            with TabPane("Transfer", id="transfer"):
                yield Label("Transfer; Seems to work!")

    # yield Footer()

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        Enables double-clicking a directory within the directory-tree
        widget to replace contents of the \'Subject\' and/or \'Session\'
        input widgets depending on the prefix of the directory selected.
        Double-click time is set to the Windows default duration (500 ms).
        """
        click_time = monotonic()
        if click_time - self.prev_click_time < 0.5:
            if event.path.stem.startswith("sub-"):
                self.query_one("#subject").value = str(event.path.stem)
            if event.path.stem.startswith("ses-"):
                self.query_one("#session").value = str(event.path.stem)
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
                self.query_one("#FileTree").reload()
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return
        if event.button.id == "return":
            self.dismiss()


class TuiApp(App):
    """
    The main app page for the DataShuttle TUI.

    Running this application in a main block as below
    if __name__ == __main__:
         app = MyApp()
         app.run()

    Initialises the TUI event loop and starts the application.

    COMBINED WITH

    This Screen contains DataShuttle's project selection splashscreen.
    From here, the user can select an existing project or begin
    initializing a new project.

    TODO: the responsibility for this window is to return a valid project
    or indicate a new project must be made.
    """

    tui_path = Path(__file__).parent
    CSS_PATH = list(Path(tui_path / "css").glob("*.tcss"))

    BINDINGS = [
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    # TODO: need to reload this dynamically when new project added
    project_names = get_existing_project_paths_and_names()[0]

    def compose(self):
        yield Container(
            Label("DataShuttle", id="main_title"),
            Label("Select project", id="name_label"),
            *[Button(name, id=name) for name in self.project_names],
            Button("New project", id="project_select_new_project_button"),
            id="test_id",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "project_select_new_project_button":
            pass
        elif event.button.id in self.project_names:
            try:
                project = DataShuttle(str(event.button.id))
            except BaseException as e:
                self.show_modal_error_dialog(str(e))
                return
            self.push_screen(TabScreen(self, project))

    def show_modal_error_dialog(self, message):
        # TODO: This `replace()` is super hacky. Will have to handle assert
        # messages centrally , depending on whether piping to GUI
        # or API / CLI.
        self.push_screen(QuitScreen(message.replace(". ", ".\n\n")))


if __name__ == "__main__":
    app = TuiApp()
    app.run()
