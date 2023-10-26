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
    RadioButton,
    RadioSet,
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


class ConfigsContent(Container):
    def __init__(self, project):
        super(ConfigsContent, self).__init__()

        self.project = project
        self.connection_method = "ssh"
        self.config_ssh_widgets = []  # TODO: check this is okay

    def compose(self):
        # Create the configs tab. If we are setting up a project
        # for the first time, Include widgets with information,
        # and for setting the project name.
        ssh_radiobutton_bool = (
            True if self.connection_method == "ssh" else False
        )
        local_filesystem_radiobutton_bool = not ssh_radiobutton_bool

        self.config_ssh_widgets = [
            Label("Central Host ID"),
            Input(
                placeholder="e.g. username", id="configs_central_host_id_input"
            ),
            Label("Central Host Username"),
            Input(
                placeholder="e.g. ssh.swc.ucl.ac.uk",
                id="configs_central_host_username_input",
            ),
        ]

        config_screen_widgets = [
            Label("Local Path", id="newproject_locpath_label"),
            Input(
                placeholder=r"e.g. C:\path\to\my_projects\my_first_project",
                id="newproject_locpath_input",
            ),
            Label("Central Path", id="newproject_centpath_label"),
            Input(
                placeholder="e.g. /central/live/username/my_projects/my_first_project",
                id="newproject_centpath_input",
            ),
            Label("Connection Method", id="newproject_connect_method_label"),
            RadioSet(
                RadioButton("SSH", value=ssh_radiobutton_bool),
                RadioButton(
                    "Local Filesystem", value=local_filesystem_radiobutton_bool
                ),
                id="newproject_connect_method_radioset",
            ),
            *self.config_ssh_widgets,
            Container(
                Checkbox(
                    "Overwrite Old Files",
                    value=False,
                    id="config_overwrite_files_checkbox",
                ),
                Checkbox(
                    "Verbose", value=False, id="config_verbosity_checkbox"
                ),
                Checkbox(
                    "Show Transfer Progress",
                    value=False,
                    id="config_transfer_progress_checkbox",
                ),
                id="config_transfer_options_container",
            ),
            Button("Configure Project", id="newproject_config_button"),
        ]

        init_only_config_screen_widgets = [
            Label("Configure New Project", id="newproject_banner_label"),
            Label(
                "Set your configurations for a new project. For more "
                "details on each section,\nsee the Datashuttle "  # TODO: are links to websites possible?
                "documentation. Once configs are set, you will "
                "be able\nto use the 'Create' and 'Transfer' tabs.",
                id="newproject_info_label",
            ),
            Label("Project Name", id="newproject_name_label"),
            Input(
                placeholder="e.g. my_first_project", id="newproject_name_input"
            ),
        ]

        if not self.project:  # TODO: how to make this explicit?
            config_screen_widgets = (
                init_only_config_screen_widgets + config_screen_widgets
            )

        yield Container(*config_screen_widgets, id="newproject_container")

    def on_mount(self):
        container = self.query_one("#config_transfer_options_container")
        container.border_title = "Transfer Options"
        if self.project:
            self.auto_fill_widgets_from_project_configs()
        self.switch_ssh_widgets_display()

    def auto_fill_widgets_from_project_configs(self):
        # TODO: or could do during setup, but will get messy...
        # Little bit redundant, but whatever...?
        input = self.query_one("#newproject_locpath_input")
        input.value = "test setup"

        input = self.query_one("#newproject_centpath_label")
        input.value = "test setup"

        input = self.query_one("#newproject_locpath_input")
        input.value = "test setup"

        # SSH

        input = self.query_one("#newproject_locpath_input")
        input.value = "test setup"

        input = self.query_one("#newproject_locpath_input")
        input.value = "test setup"

        # Checkboxes

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        # TODO: think if this formatting is robust enough.
        # I think just if == "ssh" key == "ssh" else "local_filesystem".
        format_connection_method = (
            str(event.pressed.label).lower().replace(" ", "_")
        )
        self.connection_method = format_connection_method
        self.switch_ssh_widgets_display()

    def switch_ssh_widgets_display(self):
        for widget in self.config_ssh_widgets:
            widget.display = True if self.connection_method == "ssh" else False

    def on_button_pressed(
        self, event: Button.Pressed
    ):  # TODO: can this be different for each screen?
        """
        Enables the Make Folders button to read out current input values
        and use these to call project.make_folders().
        """
        if event.button.id == "newproject_config_button":
            if not self.project:
                try:
                    project_name = self.query_one(
                        "#newproject_name_input"
                    ).value

                    project = DataShuttle(project_name)

                    # TODO: the problem with overwriting all is that if
                    # someone has ssh configs set already, the appropriate
                    # resolution is not clear. Maybe datashuttle should,
                    # if the configs are not passed, set them to what
                    # they were previously.
                    project.make_config_file(
                        local_path=self.query_one(
                            "#newproject_locpath_input"
                        ).value,
                        central_path=self.query_one(
                            "#newproject_centpath_input"
                        ).value,
                        connection_method=self.connection_method,
                    )
                    # TODO: dont use error here.
                    self.mainwindow.show_modal_error_dialog(
                        "Project setup success"
                    )
                    self.project = project

                    for widget_id in [
                        "#newproject_name_input",
                        "#newproject_name_label",
                        "#newproject_info_label",
                    ]:
                        widget = self.query(widget_id)
                        widget.remove()
                except BaseException as e:
                    self.mainwindow.show_modal_error_dialog(str(e))
            else:
                raise NotImplementedError(
                    "setting configs for existing project not implemented."
                )


class MakeNewProjectScreen(Screen):
    def __init__(self, project):
        super(MakeNewProjectScreen, self).__init__()

        self.project = project

    def compose(self):
        # TODO: decide whether setup-relevant configs only
        # should be sown here? almost, certainly.
        yield Header(id="project_select_header")
        yield Button("Main Menu", id="main_menu_button")
        yield ConfigsContent(self.project)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "main_menu_button":
            self.dismiss(False)


class TabScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.
    """

    TITLE = "Manage Project"

    prev_click_time = 0.0

    def __init__(
        self, mainwindow, project, init_project=False
    ):  # TODO: avoid weird project duck-typing if possible
        super(TabScreen, self).__init__()
        self.mainwindow = mainwindow
        self.project = project
        self.init_project = init_project
        self.tab_content = None

        if self.init_project:
            self.connection_method = "ssh"  # TODO: default value
        else:
            self.connection_method = project.cfg["connection_method"]

    def compose(self) -> ComposeResult:
        """
        Composes widgets to the TUI in the order specified.
        """
        yield Header()
        yield Button("Main Menu", id="tabscreen_main_menu_button")
        with TabbedContent(
            id="tabscreen_tabbed_content", initial="tabscreen_create_tab"
        ) as self.tab_content:
            # Create a content window with 'Create', 'Transfer' and 'Configs' tab

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
                yield DatatypeCheckboxes()
                yield Button("Make Folders", id="tabscreen_make_folder_button")

            with TabPane("Transfer", id="tabscreen_transfer_tab"):
                yield Label("Transfer; Seems to work!")

            with TabPane("Configs", id="tabscreen_configs_tab"):
                yield ConfigsContent(self.project)

    def on_mount(self) -> None:
        self.query_one("#newproject_connect_method_radioset").focus()

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
        yield Button("Main Menu", id="main_menu_button")
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
        elif event.button.id == "main_menu_buttons":
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
            self.push_screen(MakeNewProjectScreen(project=None))

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
