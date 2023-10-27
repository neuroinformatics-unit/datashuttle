import copy
from pathlib import Path
from time import monotonic

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
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


class ShowConfigsDialog(ModalScreen):
    """ """

    def __init__(self, dict_, message_before_dict=""):
        super(ShowConfigsDialog, self).__init__()

        self.dict_ = dict_
        self.message_before_dict = message_before_dict

    def compose(self):
        yield Container(
            Container(
                Static(self.message_before_dict, id="show_dict_message_label"),
                DataTable(id="modal_table", show_header=False),
                id="show_dict_message_container",
            ),
            Container(Button("OK"), id="show_dict_ok_button"),
            id="show_dict_top_container",
        )

    def on_mount(self):
        """
        start with empty header
        """
        ROWS = [("", "")] + [(key, value) for key, value in self.dict_.items()]

        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])

        for row in ROWS[1:]:
            styled_row = [Text(str(cell), justify="left") for cell in row]
            table.add_row(*styled_row)

    def on_button_pressed(self) -> None:
        """ """
        self.dismiss(None)


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
                type.title(), id=f"tabscreen_{type}_checkbox", value=True
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


def get_textual_compatible_project_configs(project_cfg):
    """
    TODO: should this function go in datashuttle? or some tui-logic
    module, probably the latter as does not make sense to mix
    tui-logic with core datashuttle logic.
    This is in place.
    """
    cfg_to_load = copy.deepcopy(project_cfg)
    project_cfg.convert_str_and_pathlib_paths(cfg_to_load, "path_to_str")
    return cfg_to_load


class ConfigsContent(Container):
    """ """

    def __init__(self, parent_class, project):
        super(ConfigsContent, self).__init__()

        self.parent_class = parent_class
        self.project = project
        self.config_ssh_widgets = []

    def compose(self):
        """
        Create the configs tab. If we are setting up a project
        for the first time, Include widgets with information,
        and for setting the project name.
        """
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
            Label("Local Path", id="newproject_local_path_label"),
            Input(
                placeholder=r"e.g. C:\path\to\my_projects\my_first_project",
                id="newproject_local_path_input",
            ),
            Label("Central Path", id="newproject_central_path_label"),
            Input(
                placeholder="e.g. /central/live/username/my_projects/my_first_project",
                id="newproject_central_path_input",
            ),
            Label("Connection Method", id="newproject_connect_method_label"),
            RadioSet(
                RadioButton(
                    "Local Filesystem", id="local_filesystem_radiobutton"
                ),
                RadioButton("SSH", id="ssh_radiobutton"),
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
            Horizontal(
                Button("Configure Project", id="newproject_config_button")
            ),  # TODO: rename
        ]

        init_only_config_screen_widgets = [
            Label("Configure A New Project", id="newproject_banner_label"),
            Horizontal(
                Static(
                    "Set your configurations for a new project. For more "
                    "details on each section,\nsee the Datashuttle "  # TODO: are links to websites possible?
                    "documentation. Once configs are set, you will "
                    "be able\nto use the 'Create' and 'Transfer' tabs.",
                    id="newproject_info_label",
                )
            ),
            Label("Project Name", id="newproject_name_label"),
            Input(
                placeholder="e.g. my_first_project", id="newproject_name_input"
            ),
        ]

        if not self.project:
            config_screen_widgets = (
                init_only_config_screen_widgets + config_screen_widgets
            )

        yield Container(*config_screen_widgets, id="newproject_container")

    def on_mount(self):
        container = self.query_one("#config_transfer_options_container")
        container.border_title = "Transfer Options"
        if self.project:
            self.fill_widgets_with_project_configs()
        else:
            radiobutton = self.query_one("#local_filesystem_radiobutton")
            radiobutton.value = True
            self.switch_ssh_widgets_display(display_bool=False)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        TODO: this isn't very robust, these aliases should be
        set centrally
        """
        display_bool = True if str(event.pressed.label) == "SSH" else False
        self.switch_ssh_widgets_display(display_bool)

    def switch_ssh_widgets_display(self, display_bool):
        for widget in self.config_ssh_widgets:
            widget.display = display_bool

    def on_button_pressed(self, event: Button.Pressed):
        """
        Enables the Make Folders button to read out current input values
        and use these to call project.make_folders().
        """
        if event.button.id == "newproject_config_button":
            if not self.project:
                self.setup_configs_for_a_new_project_and_switch_to_tab_screen()
            else:
                self.setup_configs_for_an_existing_project()

    def setup_configs_for_a_new_project_and_switch_to_tab_screen(self):
        """ """
        project_name = self.query_one("#newproject_name_input").value

        try:
            project = DataShuttle(project_name)

            cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

            project.make_config_file(**cfg_kwargs)

            self.parent_class.mainwindow.push_screen(
                ShowConfigsDialog(
                    get_textual_compatible_project_configs(project.cfg),
                    "Congratulations, you have set up DataShuttle with the below "
                    "configs.\n\nNext, you will be taken to the project page where "
                    "you can create and transfer your project folders.",
                ),
                lambda _: self.parent_class.dismiss_and_return_project(
                    project
                ),
            )

        except BaseException as e:
            self.parent_class.mainwindow.show_modal_error_dialog(str(e))

    def setup_configs_for_an_existing_project(self):
        """ """
        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        try:
            self.project.make_config_file(**cfg_kwargs)

            configs_to_show = get_textual_compatible_project_configs(
                self.project.cfg
            )

            self.parent_class.mainwindow.push_screen(
                ShowConfigsDialog(
                    configs_to_show,
                    "The Configs for the project have been set to the "
                    "following values:",
                )
            )
        except BaseException as e:
            self.parent_class.mainwindow.show_modal_error_dialog(str(e))

    def fill_widgets_with_project_configs(self):
        """ """
        cfg_to_load = get_textual_compatible_project_configs(self.project.cfg)

        # Local Path
        input = self.query_one("#newproject_local_path_input")
        input.value = cfg_to_load["local_path"]

        # Central Path
        input = self.query_one("#newproject_central_path_input")
        input.value = cfg_to_load["central_path"]

        # Connection Method
        ssh_on = True if cfg_to_load["connection_method"] == "ssh" else False

        radiobutton = self.query_one("#ssh_radiobutton")
        radiobutton.value = ssh_on

        radiobutton = self.query_one("#local_filesystem_radiobutton")
        radiobutton.value = not ssh_on

        self.switch_ssh_widgets_display(display_bool=ssh_on)

        # Central Host ID
        input = self.query_one("#configs_central_host_id_input")
        value = (
            ""
            if cfg_to_load["central_host_id"] is None
            else cfg_to_load["central_host_id"]
        )
        input.value = value

        # Central Host Username
        input = self.query_one("#configs_central_host_username_input")
        value = (
            ""
            if cfg_to_load["central_host_username"] is None
            else cfg_to_load["central_host_username"]
        )
        input.value = value

        # Overwrite Files Checkbox
        checkbox = self.query_one("#config_overwrite_files_checkbox")
        checkbox.value = self.project.cfg["overwrite_old_files"]

        # Transfer Verbosity
        checkbox = self.query_one("#config_verbosity_checkbox")
        bool = True if self.project.cfg["transfer_verbosity"] == "v" else False
        checkbox.value = bool

        # Show Transfer Progress
        checkbox = self.query_one("#config_transfer_progress_checkbox")
        checkbox.value = self.project.cfg["show_transfer_progress"]

    def get_datashuttle_inputs_from_widgets(self):
        """ """
        cfg_kwargs = {}

        cfg_kwargs["local_path"] = self.query_one(
            "#newproject_local_path_input"
        ).value

        cfg_kwargs["central_path"] = self.query_one(
            "#newproject_central_path_input"
        ).value

        cfg_kwargs["connection_method"] = (
            "ssh"
            if self.query_one("#ssh_radiobutton").value
            else "local_filesystem"
        )

        cfg_kwargs["central_host_id"] = self.query_one(
            "#configs_central_host_id_input"
        ).value

        cfg_kwargs["central_host_username"] = self.query_one(
            "#configs_central_host_username_input"
        ).value

        cfg_kwargs["overwrite_old_files"] = self.query_one(
            "#config_overwrite_files_checkbox"
        ).value

        verbosity_kwarg = (
            "vv" if self.query_one("#config_verbosity_checkbox").value else "v"
        )
        cfg_kwargs["transfer_verbosity"] = verbosity_kwarg

        cfg_kwargs["show_transfer_progress"] = self.query_one(
            "#config_transfer_progress_checkbox"
        ).value

        return cfg_kwargs


class NewProjectScreen(Screen):
    """ """

    TITLE = "Make New Project"

    def __init__(self, mainwindow):
        super(NewProjectScreen, self).__init__()

        self.mainwindow = mainwindow
        self.configs_page = ConfigsContent(self, project=None)

    def compose(self):
        yield Header()
        yield Button("Main Menu", id="main_menu_button")
        yield self.configs_page

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "main_menu_button":
            self.dismiss(False)

    def dismiss_and_return_project(self, project):
        self.dismiss(project)


class TabScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.
    """

    TITLE = "Manage Project"

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
        yield Button("Main Menu", id="main_menu_button")
        with TabbedContent(
            id="tabscreen_tabbed_content", initial="tabscreen_create_tab"
        ):
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
                yield ConfigsContent(self, self.project)

    def on_mount(self) -> None:
        self.title = f"Project: {self.project.project_name}"

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

        elif event.button.id == "main_menu_button":
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
        elif event.button.id == "main_menu_button":
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
        """ """
        if event.button.id == "mainwindow_existing_project_button":
            self.push_screen(ProjectSelector(self), self.load_project_page)

        elif event.button.id == "mainwindow_new_project_button":
            self.push_screen(
                NewProjectScreen(self),
                self.load_project_page,
            )

    def load_project_page(self, project):
        if project:
            self.push_screen(TabScreen(self, project))

    def show_modal_error_dialog(self, message):
        self.push_screen(ErrorScreen(message))


if __name__ == "__main__":
    TuiApp().run()
