from pathlib import Path
from time import monotonic
from textual import on
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
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from datashuttle import DataShuttle
from datashuttle.configs.canonical_configs import get_datatypes
from datashuttle.utils.folders import get_existing_project_paths_and_names


class ErrorScreen(ModalScreen):
    """
    Screen that renders a modal dialog window (a pop up window that
    means no other widgets can be changed until it is closed).
    """

    def __init__(self, message):
        super(ErrorScreen, self).__init__()

        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Static(self.message, id="errorscreen_message_label"),
                id="errorscreen_message_container",
            ),
            Container(Button("OK"), id="errorscreen_ok_button"),
            id="errorscreen_top_container",
        )

    def on_button_pressed(self) -> None:
        self.dismiss()


class DatatypeCheckboxes(Static):
    """
    Dynamically-populated checkbox widget for convenient datatype
    selection during folder creation.

    Attributes
    ----------

    type_out:
        List of datatypes selected by the user to be passed to `make_folders`
        (e.g. "behav" that will be passed to `make-folders`.)

    type_config:
        List of datatypes supported by NeuroBlueprint
    """

    type_out = reactive("all")

    def __init__(self):
        super(DatatypeCheckboxes, self).__init__()

        self.type_config = get_datatypes()

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
            type: self.query_one(f"#tabscreen_{type}_checkbox").value
            for type in self.type_config
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

    TITLE = "Manage Project"

    prev_click_time = 0.0

    def __init__(self, mainwindow, project, init_project=False):
        super(TabScreen, self).__init__()
        self.mainwindow = mainwindow
        self.project = project
        self.init_project = init_project
        self.tab_content = None
        self.connection_method = "ssh" # TODO: default value

    def compose(self) -> ComposeResult:
        """
        Composes widgets to the TUI in the order specified.
        """
        directory_tree_root = "" if self.init_project else str(self.project.cfg.data["local_path"])
        initial = "tabscreen_configs_tab" if self.init_project else "tabscreen_create_tab"
        disable_create_and_transfer = True if self.init_project else False

        yield Header()
        yield Button("Main Menu", id="tabscreen_main_menu_button")
        with TabbedContent(id="tabscreen_tabbed_content",  initial=initial) as self.tab_content:
            with TabPane("Create", id="tabscreen_create_tab", disabled=disable_create_and_transfer):
                yield DirectoryTree(
                    directory_tree_root,
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
                yield DatatypeCheckboxes()
                yield Button("Make Folders", id="tabscreen_make_folder_button")
            with TabPane("Transfer", id="tabscreen_transfer_tab", disabled=disable_create_and_transfer):
                yield Label("Transfer; Seems to work!")
            with TabPane("Configs", id="tabscreen_configs_tab"):
                widgets_to_include = [
                    Label("Local Path", id="newproject_locpath_label"),
                    Input(
                        placeholder="e.g. C:/User/Documents",
                        id="newproject_locpath_input",
                    ),
                    Label("Central Path", id="newproject_centpath_label"),
                    Input(
                        placeholder="e.g. X:/Some/Path", id="newproject_centpath_input"
                    ),
                    Label("Connection Method", id="newproject_connect_method_label"),
                    Select(
                        [("SSH", "ssh"), ("Local Filesystem", "local_filesystem")],
                        prompt="Select connection method",
                        id="newproject_connect_method_select",  # TODO: use radio button, set  default to self.conenction_method
                    ),
                    Button("Configure Project", id="newproject_config_button")
                ]

                if self.init_project:
                    yield Container(Label("Set your configurations for a new project. For more "
                                          "details on each section,\nsee the Datashuttle "  # TODO: are links to websites possible?
                                          "documentation. Once configs are set, you will "
                                          "be able\nto use the 'Create' and 'Transfer' tabs.",
                                          id="newproject_info_label"),
                              Label("Project Name", id="newproject_name_label"),
                              Input(placeholder="e.g. MyProject123",
                                          id="newproject_name_input"),
                              *widgets_to_include, id = "newproject_container")
                else:
                    yield Container(*widgets_to_include, id = "newproject_container")

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
            # TODO: own function
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
        elif event.button.id == "tabscreen_main_menu_button":
            self.dismiss()

        elif event.button.id == "newproject_config_button":

            if self.init_project:
                # TODO: own function
                assert self.connection_method == "local_filesystem", "'ssh' connection method not implemented yet."

                try:
                    project_name = self.query_one("#newproject_name_input").value
                    from datashuttle import DataShuttle

                    project = DataShuttle(project_name)

                    project.make_config_file(
                        local_path=self.query_one("#newproject_locpath_input").value,
                        central_path=self.query_one("#newproject_centpath_input").value,
                        connection_method=self.connection_method,
                    )
                    self.mainwindow.show_modal_error_dialog("Project setup success")  # TODO: dont use error here.
                    self.project = project
                    self.tab_content.enable_tab("tabscreen_create_tab")
                    self.tab_content.enable_tab("tabscreen_transfer_tab")
                    self.init_project = False
                    for widget_id in ["#newproject_name_input",
                                      "#newproject_name_input",
                                      "#newproject_info_label"]:
                        widget = self.query(widget_id)
                        widget.remove()
                except BaseException as e:
                    self.mainwindow.show_modal_error_dialog(str(e))
            else:
                raise NotImplementedError("setting configs for existing project not implemented.")

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.connection_method = str(event.value)


class ProjectSelector(Screen):
    """
    The DataShuttle TUI's project selection screen. Finds and displays
    DataShuttle projects present on the local system.
    """

    TITLE = "Select Project"

    def __init__(self, mainwindow):
        super(ProjectSelector, self).__init__()

        self.project_names = get_existing_project_paths_and_names()[0]
        self.mainwindow = mainwindow

    def compose(self):
        yield Header(id="project_select_header")
        yield Button("Main Menu", id="project_select_main_menu_button")
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
        elif event.button.id == "project_select_main_menu_button":
            self.dismiss(False)


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
        if event.button.id == "mainwindow_existing_project_button":
            self.push_screen(ProjectSelector(self), self.load_project_page)
        elif event.button.id == "mainwindow_new_project_button":
            self.load_project_page(True, init_project=True)  # TODO: jenky

    def load_project_page(self, project, init_project=False):
        if project:
            self.push_screen(TabScreen(self, project, init_project))

    def show_modal_error_dialog(self, message):
        # TODO: This `replace()` is super hacky. Will have to handle assert
        # messages centrally , depending on whether piping to GUI
        # or API / CLI.
        self.push_screen(ErrorScreen(message.replace(". ", ".\n\n")))


if __name__ == "__main__":
    TuiApp().run()
