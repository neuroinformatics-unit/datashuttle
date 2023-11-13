from pathlib import Path
from time import monotonic

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import (
    Button,
    DirectoryTree,
    Header,
    Input,
    Label,
    TabbedContent,
    TabPane,
)

from datashuttle import DataShuttle
from datashuttle.tui import custom_widgets, project_config
from datashuttle.utils.folders import get_existing_project_paths_and_names

# RENAME ALL WIDGETS
# TCSS


class TabScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.

    The 'Create' tab interacts with Datashuttle's `make_folders()`
    method to create new project folders.

    The 'Transfer' tab, XXX.

    The 'Configs' tab displays the current project's configurations
    and allows configs to be reset. This is an instantiation of the
    ConfigsContent window, which is also shared by `Make New Project`.
    See ConfigsContent for more information.

    Parameters
    ----------

    mainwindow : TuiApp
        The main application window used for coordinating screen display.

    project : DataShuttle
        An instantiated datashuttle project.
    """

    prev_click_time = 0.0

    def __init__(self, mainwindow, project):
        super(TabScreen, self).__init__()

        self.mainwindow = mainwindow
        self.project = project
        self.title = f"Project: {self.project.project_name}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Main Menu", id="all_main_menu_buttons")
        with TabbedContent(
            id="tabscreen_tabbed_content", initial="tabscreen_create_tab"
        ):
            with TabPane("Create", id="tabscreen_create_tab"):
                yield DirectoryTree(
                    self.project.cfg.data["local_path"],
                    id="tabscreen_directorytree",
                )
                yield Label("Subject(s)", id="tabscreen_subject_label")
                yield Input(
                    id="tabscreen_subject_input", placeholder="e.g. sub-001"
                )
                yield Label("Session(s)", id="tabscreen_session_label")
                yield Input(
                    id="tabscreen_session_input", placeholder="e.g. ses-001"
                )
                yield Label("Datatype(s)", id="tabscreen_datatype_label")
                yield custom_widgets.DatatypeCheckboxes()
                yield Button("Make Folders", id="tabscreen_make_folder_button")

            with TabPane("Transfer", id="tabscreen_transfer_tab"):
                yield Label("Transfer; Seems to work!")

            with TabPane("Configs", id="tabscreen_configs_tab"):
                yield project_config.ConfigsContent(self, self.project)

    # TODO: the upcoming refactor will be super nice because the logic
    # that handles button presses can be split across the relevant
    # tab classes.
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        Upon double-clicking a directory within the directory-tree
        widget, replace contents of the \'Subject\' and/or \'Session\'
        input widgets, depending on the prefix of the directory selected.
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
        Enables the Make Folders button to read out current input values
        and use these to call project.make_folders().
        """
        if event.button.id == "tabscreen_make_folder_button":
            sub_dir = self.query_one("#tabscreen_subject_input").value
            ses_dir = self.query_one("#tabscreen_session_input").value

            try:
                self.project.make_folders(
                    sub_names=sub_dir,
                    ses_names=ses_dir,
                    datatype=self.query_one("DatatypeCheckboxes").type_out,
                )
                self.query_one("#tabscreen_directorytree").reload()
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return

        elif event.button.id == "all_main_menu_buttons":
            self.dismiss()


class ProjectSelector(Screen):
    """
    The project selection screen. Finds and displays DataShuttle
    projects present on the local system.

    `self.dismiss()` returns an initialised project if initialisation
    was successful. Otherwise, in case "Main Menu` button is pressed,
    returns None to return without effect to the main menu.,

    Parameters
    ----------

    mainwindow : TuiApp
        The main TUI app, functions on which are used to coordinate
        screen display.

    """

    TITLE = "Select Project"

    def __init__(self, mainwindow):
        super(ProjectSelector, self).__init__()

        self.project_names = get_existing_project_paths_and_names()[0]
        self.mainwindow = mainwindow

    def compose(self):
        yield Header(id="project_select_header")
        yield Button("Main Menu", id="all_main_menu_buttons")
        yield Container(
            *[Button(name, id=name) for name in self.project_names],
            id="project_select_top_container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id in self.project_names:
            try:
                project = DataShuttle(str(event.button.id))
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return
            self.dismiss(project)

        elif event.button.id == "all_main_menu_buttons":
            self.dismiss(False)


class TuiApp(App):
    """
    The main app page for the DataShuttle TUI.

    This class acts as a base class from which all windows
    (select existing project, make new project, settings and
    get help) are raised.

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

    def compose(self):
        yield Container(
            Label("DataShuttle", id="mainwindow_banner_label"),
            Button(
                "Select Existing Project",
                id="mainwindow_existing_project_button",
            ),
            Button("Make New Project", id="mainwindow_new_project_button"),
            Button("Settings", id="mainwindow_settings_button"),
            Button("Get Help", id="mainwindow_get_help_button"),
            id="mainwindow_contents_container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        """
        When a button is pressed, a new screen is displayed with
        `push_screen`. The second argument is a callback to
        load the project page, with an initialised project
        or `None` (in case no project was selected).

        Error handling is at the level of the individual screens,
        but presentation of the error dialog is handled in
        `self.show_modal_error_dialog()`.
        """
        if event.button.id == "mainwindow_existing_project_button":
            self.push_screen(ProjectSelector(self), self.load_project_page)

        elif event.button.id == "mainwindow_new_project_button":
            self.push_screen(
                project_config.NewProjectScreen(self),
                self.load_project_page,
            )

    def load_project_page(self, project):
        if project:
            self.push_screen(TabScreen(self, project))

    def show_modal_error_dialog(self, message):
        self.push_screen(custom_widgets.ErrorScreen(message))


if __name__ == "__main__":
    TuiApp().run()
