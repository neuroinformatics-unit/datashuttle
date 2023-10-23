from pathlib import Path
from time import monotonic

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from datashuttle import DataShuttle
from datashuttle.utils.folders import get_existing_project_paths_and_names


class TypeBox_Static(Static):
    def compose(self):
        yield Checkbox("Ephys", id="ephys")
        yield Checkbox("Behav", id="behav")
        yield Checkbox("FuncImg", id="funcimg")
        yield Checkbox("Histology", id="histo")


class NewProject(Screen):
    """
    Screen object from which a new datashuttle project can be initialized.
    Appears when 'New Project' is clicked on the project selection screen.
    """

    def compose(self):
        yield Label("Configure New Project", id="title")
        yield Label("Project Name")
        yield Input(placeholder="e.g. MyProject123", id="ProjectName")
        yield Label("Local Path")
        yield Input(placeholder="e.g. C:/User/Documents", id="LocalPath")
        yield Label("Central Path")
        yield Input(placeholder="e.g. X:/Some/Path", id="CentralPath")
        yield Label("Connection Method")
        yield Select(
            [("SSH", "ssh"), ("Local Filesystem", "local_filesystem")],
            prompt="Select connection method",
            id="ConnectMethod",
        )
        yield Label("Select Datatypes")
        yield TypeBox_Static()
        yield Button("Configure Project", id="config")
        yield Button("Return", id="return")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "return":
            app.pop_screen()
        if event.button.id == "config":
            pass
            # project = DataShuttle(self.query_one("#ProjectName").value)
            # project.make_config_file(
            #     local_path = self.query_one("#LocalPath").value,
            #     central_path = self.query_one("#CentralPath").value,
            #     connection_method = self.query_one("#ConnectMethod"),
            #     use_ephys = bool(self.query_one("TypeBox_Static").query_one("#ephys").value),
            #     use_behav = bool(self.query_one("TypeBox_Static").query_one("#behav").value),
            #     use_funcimg = bool(self.query_one("TypeBox_Static").query_one("#funcimg").value),
            #     use_histology = bool(self.query_one("TypeBox_Static").query_one("#histo").value)
            # )
            # app.project = project
            # app.switch_screen(TabScreen())


class ProjectSelect(Screen):
    """
    This Screen contains DataShuttle's project selection splashscreen.
    From here, the user can select an existing project or begin
    initializing a new project.
    """

    TITLE = "Select Project"

    def __init__(self):
        super(ProjectSelect, self).__init__()
        self.project_names = get_existing_project_paths_and_names()[0]

    def compose(self):
        yield Label("DataShuttle", id="main_title")
        yield Label("Select project", id="name_label")
        for name in self.project_names:
            yield Button(name, id=name)
        yield Button("New project", id="new_project")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "new_project":
            app.push_screen(NewProject())
        else:
            app.project = DataShuttle(str(event.button.id))
            app.push_screen(TabScreen())


class TypeBox_Dynamic(Static):
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
        super(TypeBox_Dynamic, self).__init__()

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

    def __init__(self):
        super(TabScreen, self).__init__()
        self.project = app.project

    def compose(self) -> ComposeResult:
        """
        Composes widgets to the TUI in the order specified.
        """
        yield Header()
        yield Button("Return", id="return")
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
                yield TypeBox_Dynamic(self.project.cfg)
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
                self.query_one("#FileTree").reload()
            except BaseException as e:
                self.query_one("#errors_on_create_page").value = str(e)

        if event.button.id == "return":
            app.pop_screen()


class TuiApp(App):
    """
    The main app page for the DataShuttle TUI.

    Running this application in a main block as below
    if __name__ == __main__:
         app = MyApp()
         app.run()

    Initialises the TUI event loop and starts the application.
    """

    tui_path = Path(__file__).parent
    CSS_PATH = list(Path(tui_path / "css").glob("*.tcss"))

    BINDINGS = [
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    def on_ready(self):
        self.push_screen(ProjectSelect())


if __name__ == "__main__":
    app = TuiApp()
    app.run()
