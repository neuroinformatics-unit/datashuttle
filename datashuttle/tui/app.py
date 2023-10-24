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
    """
    Screen that renders a modal dialog window (a pop up window that
    means no other widgets can be changed until it is closed).
    """

    def __init__(self, message):
        super(QuitScreen, self).__init__()

        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Static(self.message, id="quitscreen_message_label"),
                id="quitscreen_message_container",
            ),
            Container(Button("OK"), id="quitscreen_ok_button"),
            id="quitscreen_top_container",
        )

    def on_button_pressed(self) -> None:
        self.dismiss()


class TabScreenCheckboxes(Static):
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
        super(TabScreenCheckboxes, self).__init__()

        self.type_config = [
            config.removeprefix("use_")
            for config, is_on in zip(project_cfg.keys(), project_cfg.values())
            if "use_" in config and is_on
        ]

    def compose(self):
        for type in self.type_config:
            yield Checkbox(
                type.title(), id=f"tabscreen_{type}_checkbox", value=1
            )

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
        yield Button("Main Menu", id="tabscreen_main_menu_button")
        with TabbedContent():
            with TabPane("Create", id="tabscreen_create_tab"):
                yield DirectoryTree(
                    str(self.project.cfg.data["local_path"]),
                    id="tabscreen_directorytree",
                )
                yield Label("Subject(s)", id="tabscreen_subject_label")
                yield Input(
                    id="tabscreen_subject_input", placeholder="e.g. sub-001"
                )
                yield Label("Session(s)")
                yield Input(
                    id="tabscreen_session_input", placeholder="e.g. ses-001"
                )
                yield Label("Datatype(s)")
                yield TabScreenCheckboxes(self.project.cfg)
                yield Button("Make Folders", id="tabscreen_make_folder_button")
            with TabPane("Transfer", id="tabscreen_transfer_tab"):
                yield Label("Transfer; Seems to work!")

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
                self.query_one("#tabscreen_subject_input").value = str(
                    event.path.stem
                )
            if event.path.stem.startswith("ses-"):
                self.query_one("#tabscreen_session_input").value = str(
                    event.path.stem
                )
        self.prev_click_time = click_time

    def on_button_pressed(self, event: Button.Pressed):
        """
        Enables the Make Folder button to read out current input values
        and use these to call project.make_folders().
        """
        if event.button.id == "tabscreen_make_folder_button":
            sub_dir = self.query_one("#tabscreen_subject_input").value
            ses_dir = self.query_one("#tabscreen_session_input").value

            try:
                self.project.make_folders(
                    sub_names=sub_dir,
                    ses_names=ses_dir,
                    datatype=self.query_one("TabScreenCheckboxes").type_out,
                )
                self.query_one("#tabscreen_directorytree").reload()
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return
        if event.button.id == "tabscreen_main_menu_button":
            self.dismiss()


class TuiApp(App):
    """
    The main app page for the DataShuttle TUI.

    This Screen contains DataShuttle's project selection splashscreen.
    From here, the user can select an existing project or begin
    initializing a new project.

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

    # TODO: need to reload this dynamically when new project added
    project_names = get_existing_project_paths_and_names()[0]

    def compose(self):
        yield Container(
            Label("DataShuttle", id="mainwindow_main_title_label"),
            Label("Select project", id="mainwindow_select_project_label"),
            *[Button(name, id=name) for name in self.project_names],
            Button("New project", id="mainwindow_select_new_project_button"),
            id="mainwindow_top_container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "mainwindow_select_new_project_button":
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
