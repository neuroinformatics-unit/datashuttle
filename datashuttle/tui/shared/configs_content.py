from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface
    from datashuttle.tui.screens.new_project import NewProjectScreen
    from datashuttle.tui.screens.project_manager import ProjectManagerScreen

from dataclasses import dataclass
from pathlib import Path

from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import (
    Button,
    Label,
    RadioButton,
    RadioSet,
    Static,
)

from datashuttle.tui.custom_widgets import ClickableInput
from datashuttle.tui.interface import Interface
from datashuttle.tui.screens import (
    modal_dialogs,
    setup_aws,
    setup_gdrive,
    setup_ssh,
)
from datashuttle.tui.tooltips import get_tooltip


class ConfigsContent(Container):
    """
    This screen holds widgets and logic for setting datashuttle configs.
    It is used in `NewProjectPage` to instantiate a new project and
    initialise configs, or in `TabbedContent` to update an existing
    project's configs.

    If no project exists, additional widgets are shown to allow
    entry of a project name for new project initialisation, and
    additional information.

    Otherwise, widgets are filled with the existing projects configs.
    """

    @dataclass
    class ConfigsSaved(Message):
        pass

    def __init__(
        self,
        parent_class: Union[ProjectManagerScreen, NewProjectScreen],
        interface: Optional[Interface],
        id: str,
    ) -> None:
        super(ConfigsContent, self).__init__(id=id)

        self.parent_class = parent_class
        self.interface = interface
        self.config_ssh_widgets: List[Any] = []
        self.config_aws_widgets: List[Any] = []
        self.config_gdrive_widgets: List[Any] = []

    def compose(self) -> ComposeResult:
        """
        `self.config_ssh_widgets` are SSH-setup related widgets
        that are only required when the user selects the SSH
        connection method. These are displayed / hidden based on the
        `connection_method`

        `self.config_aws_widgets` are AWS-setup related widgets
        that are only required when the user selects the AWS S3
        connection method.

        `self.config_gdrive_widgets` are Google Drive-setup related widgets
        that are only required when the user selects the Google Drive
        connection method.

        `config_screen_widgets` are core config-related widgets that are
        always displayed.

        `init_only_config_screen_widgets` are only displayed if we
        are instantiating a new project.
        """
        self.config_ssh_widgets = [
            Label("Central Host ID", id="configs_central_host_id_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. ssh.swc.ucl.ac.uk",
                id="configs_central_host_id_input",
            ),
            Label(
                "Central Host Username",
                id="configs_central_host_username_label",
            ),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. username",
                id="configs_central_host_username_input",
            ),
        ]

        self.config_aws_widgets = [
            Label("AWS Bucket Name", id="configs_aws_bucket_name_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. my-datashuttle-bucket",
                id="configs_aws_bucket_name_input",
            ),
            Label("AWS Region", id="configs_aws_region_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. us-west-2",
                id="configs_aws_region_input",
            ),
        ]

        self.config_gdrive_widgets = [
            Label(
                "Google Drive Folder ID", id="configs_gdrive_folder_id_label"
            ),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. 0BwwA4oUTeiV1TGRPeTVjaWRDY1E",
                id="configs_gdrive_folder_id_input",
            ),
        ]

        config_screen_widgets = [
            Label("Local Path", id="configs_local_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=f"e.g. {self.get_platform_dependent_example_paths('local')}",
                    id="configs_local_path_input",
                ),
                Button("Select", id="configs_local_path_select_button"),
                id="configs_local_path_button_input_container",
            ),
            Label("Connection Method", id="configs_connect_method_label"),
            RadioSet(
                RadioButton(
                    "Local Filesystem",
                    id="configs_local_filesystem_radiobutton",
                ),
                RadioButton("SSH", id="configs_ssh_radiobutton"),
                RadioButton("AWS S3", id="configs_aws_radiobutton"),
                RadioButton("Google Drive", id="configs_gdrive_radiobutton"),
                RadioButton(
                    "No connection (local only)",
                    id="configs_local_only_radiobutton",
                ),
                id="configs_connect_method_radioset",
            ),
            *self.config_ssh_widgets,
            *self.config_aws_widgets,
            *self.config_gdrive_widgets,
            Label("Central Path", id="configs_central_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=f"e.g. {self.get_platform_dependent_example_paths('central', ssh=False)}",
                    id="configs_central_path_input",
                ),
                Button("Select", id="configs_central_path_select_button"),
                id="configs_central_path_button_input_container",
            ),
            Horizontal(
                Button("Save", id="configs_save_configs_button"),
                Button(
                    "Setup SSH Connection",
                    id="configs_setup_ssh_connection_button",
                ),
                id="configs_primary_buttons_horizontal",
            ),
            # Second row of buttons - Cloud services and navigation
            Horizontal(
                Button(
                    "Setup AWS Connection",
                    id="configs_setup_aws_connection_button",
                ),
                Button(
                    "Setup Google Drive Connection",
                    id="configs_setup_gdrive_connection_button",
                ),
                Button(
                    "Go to Project Screen",
                    id="configs_go_to_project_screen_button",
                ),
                id="configs_secondary_buttons_horizontal",
            ),
        ]

        init_only_config_screen_widgets = [
            Label("Make A New Project", id="configs_banner_label"),
            Horizontal(
                Static(
                    "Set your configurations for a new project. For more "
                    "details on each section,\nsee the Datashuttle "
                    "documentation. Once configs are set, you will "
                    "be able\nto use the 'Create' and 'Transfer' tabs.",
                    id="configs_info_label",
                ),
                id="configs_info_label_container",
            ),
            Label("Project Name", id="configs_name_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. my_first_project",
                id="configs_name_input",
            ),
        ]

        if not self.interface:
            config_screen_widgets = (
                init_only_config_screen_widgets + config_screen_widgets
            )

        yield Container(*config_screen_widgets, id="configs_container")

    def on_mount(self) -> None:
        """
        When we have mounted the widgets, the following logic depends on whether
        we are setting up a new project (`self.project is `None`) or have
        an instantiated project.

        If we have a project, then we want to fill the widgets with the existing
        configs. Otherwise, we set to some reasonable defaults, required to
        determine the display of SSH widgets. "overwrite_files_checkbox"
        should be off by default anyway if `value` is not set, but we set here
        anyway as it is critical this is not on by default.
        """
        self.query_one("#configs_go_to_project_screen_button").visible = False

        self.query_one("#configs_setup_ssh_connection_button").visible = False
        self.query_one("#configs_setup_aws_connection_button").visible = False
        self.query_one("#configs_setup_gdrive_connection_button").visible = (
            False
        )
        if self.interface:
            self.fill_widgets_with_project_configs()
        else:
            self.query_one("#configs_local_filesystem_radiobutton").value = (
                True
            )
            self.switch_connection_widgets_display("local_filesystem")

        # Setup tooltips
        if not self.interface:
            id = "#configs_name_input"
            self.query_one(id).tooltip = get_tooltip(id)

            # Assumes 'local_filesystem' is default if no project set.
            assert (
                self.query_one("#configs_local_filesystem_radiobutton").value
                is True
            )
            self.set_central_path_input_tooltip("local_filesystem")
        else:
            connection_method = self.interface.project.cfg["connection_method"]
            self.set_central_path_input_tooltip(connection_method)

        for id in [
            "#configs_local_path_input",
            "#configs_connect_method_label",
            "#configs_local_filesystem_radiobutton",
            "#configs_ssh_radiobutton",
            "#configs_aws_radiobutton",
            "#configs_gdrive_radiobutton",
            "#configs_local_only_radiobutton",
            "#configs_central_host_username_input",
            "#configs_central_host_id_input",
            "#configs_aws_bucket_name_input",
            "#configs_aws_region_input",
            "#configs_gdrive_folder_id_input",
        ]:
            self.query_one(id).tooltip = get_tooltip(id)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        Update the displayed connection widgets when the `connection_method`
        radiobuttons are changed.

        When SSH, AWS, or Google Drive is set, respective config-setters are shown.
        Otherwise, these are hidden.

        When mode is `No connection`, the `central_path` is cleared and
        disabled.
        """
        label = str(event.pressed.label)
        assert label in [
            "SSH",
            "Local Filesystem",
            "AWS S3",
            "Google Drive",
            "No connection (local only)",
        ], "Unexpected label."

        if label == "No connection (local only)":
            self.query_one("#configs_central_path_input").value = ""
            self.query_one("#configs_central_path_input").disabled = True
            self.query_one("#configs_central_path_select_button").disabled = (
                True
            )
            connection_method = None
        else:
            self.query_one("#configs_central_path_input").disabled = False
            self.query_one("#configs_central_path_select_button").disabled = (
                False
            )
            if label == "SSH":
                connection_method = "ssh"
            elif label == "AWS S3":
                connection_method = "aws"
            elif label == "Google Drive":
                connection_method = "gdrive"
            else:
                connection_method = "local_filesystem"

        self.switch_connection_widgets_display(connection_method)
        self.set_central_path_input_tooltip(connection_method)

    def set_central_path_input_tooltip(
        self, connection_method: Optional[str]
    ) -> None:
        """
        Use a different tooltip depending on connection method.
        """
        id = "#configs_central_path_input"
        if connection_method == "ssh":
            self.query_one(id).tooltip = get_tooltip(
                "config_central_path_input_mode-ssh"
            )
        elif connection_method == "aws":
            self.query_one(id).tooltip = get_tooltip(
                "config_central_path_input_mode-aws"
            )
        elif connection_method == "gdrive":
            self.query_one(id).tooltip = get_tooltip(
                "config_central_path_input_mode-gdrive"
            )
        else:
            self.query_one(id).tooltip = get_tooltip(
                "config_central_path_input_mode-local_filesystem"
            )

    def get_platform_dependent_example_paths(
        self, local_or_central: Literal["local", "central"], ssh: bool = False
    ) -> str:
        """ """
        assert local_or_central in ["local", "central"]

        # Handle the ssh central case separately
        # because it is always the same
        if local_or_central == "central" and ssh:
            example_path = "/nfs/path_on_server/myprojects/central"
        else:
            if platform.system() == "Windows":
                example_path = rf"C:\path\to\{local_or_central}\my_projects\my_first_project"
            else:
                example_path = (
                    f"/path/to/{local_or_central}/my_projects/my_first_project"
                )

        return example_path

    def switch_connection_widgets_display(
        self, connection_method: Optional[str]
    ) -> None:
        """
        Show or hide connection-related configs based on the current
        `connection_method` widget.

        Parameters
        ----------
        connection_method : Optional[str]
            The connection method type ("ssh", "aws", "gdrive", "local_filesystem", or None)
        """
        for widget in self.config_ssh_widgets:
            widget.display = False

        for widget in self.config_aws_widgets:
            widget.display = False

        for widget in self.config_gdrive_widgets:
            widget.display = False

        self.query_one("#configs_setup_ssh_connection_button").visible = False
        self.query_one("#configs_setup_aws_connection_button").visible = False
        self.query_one("#configs_setup_gdrive_connection_button").visible = (
            False
        )

        # Show widgets based on connection method
        if connection_method == "ssh":
            for widget in self.config_ssh_widgets:
                widget.display = True
            if self.interface is not None:
                self.query_one(
                    "#configs_setup_ssh_connection_button"
                ).visible = True
        elif connection_method == "aws":
            for widget in self.config_aws_widgets:
                widget.display = True
            if self.interface is not None:
                self.query_one(
                    "#configs_setup_aws_connection_button"
                ).visible = True
        elif connection_method == "gdrive":
            for widget in self.config_gdrive_widgets:
                widget.display = True
            if self.interface is not None:
                self.query_one(
                    "#configs_setup_gdrive_connection_button"
                ).visible = True

        self.query_one("#configs_central_path_select_button").display = (
            connection_method != "ssh"
        )

        if not self.query_one("#configs_central_path_input").value:
            if connection_method == "ssh":
                placeholder = f"e.g. {self.get_platform_dependent_example_paths('central', ssh=True)}"
            else:
                placeholder = f"e.g. {self.get_platform_dependent_example_paths('central', ssh=False)}"
            self.query_one("#configs_central_path_input").placeholder = (
                placeholder
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Enables the Create Folders button to read out current input values
        and use these to call project.create_folders().
        """
        if event.button.id == "configs_save_configs_button":
            if not self.interface:
                self.setup_configs_for_a_new_project()
            else:
                self.setup_configs_for_an_existing_project()

        elif event.button.id == "configs_setup_ssh_connection_button":
            self.setup_ssh_connection()

        elif event.button.id == "configs_setup_aws_connection_button":
            self.setup_aws_connection()

        elif event.button.id == "configs_setup_gdrive_connection_button":
            self.setup_gdrive_connection()

        elif event.button.id == "configs_go_to_project_screen_button":
            self.parent_class.dismiss(self.interface)

        elif event.button.id in [
            "configs_local_path_select_button",
            "configs_central_path_select_button",
        ]:
            input_to_fill: Literal["local", "central"] = (
                "local"
                if event.button.id == "configs_local_path_select_button"
                else "central"
            )

            self.parent_class.mainwindow.push_screen(
                modal_dialogs.SelectDirectoryTreeScreen(
                    self.parent_class.mainwindow
                ),
                lambda path_: self.handle_input_fill_from_select_directory(
                    path_, input_to_fill
                ),
            )

    def handle_input_fill_from_select_directory(
        self, path_: Path, local_or_central: Literal["local", "central"]
    ) -> None:
        """
        Update the `local` or `central` path inputs after
        `SelectDirectoryTreeScreen` returns a path.

        Parameters
        ----------

        path_ : Union[Literal[False], Path]
            The path returned from `SelectDirectoryTreeScreen`. If `False`,
            the screen exited with no directory selected.

        local_or_central : str
            The Input to fill with the path.
        """
        if path_ is False:
            return

        if local_or_central == "local":
            self.query_one("#configs_local_path_input").value = (
                path_.as_posix()
            )
        elif local_or_central == "central":
            self.query_one("#configs_central_path_input").value = (
                path_.as_posix()
            )

    def setup_ssh_connection(self) -> None:
        """
        Set up the `SetupSshScreen` screen,
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        if not self.widget_configs_match_saved_configs():
            self.parent_class.mainwindow.show_modal_error_dialog(
                "The values set above must equal the datashuttle settings. "
                "Either press 'Save' or reload this page."
            )
            return

        self.parent_class.mainwindow.push_screen(
            setup_ssh.SetupSshScreen(self.interface)
        )

    def setup_aws_connection(self) -> None:
        """
        Set up the `SetupAwsScreen` screen,
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        if not self.widget_configs_match_saved_configs():
            self.parent_class.mainwindow.show_modal_error_dialog(
                "The values set above must equal the datashuttle settings. "
                "Either press 'Save' or reload this page."
            )
            return

        self.parent_class.mainwindow.push_screen(
            setup_aws.SetupAwsScreen(self.interface)
        )

    def setup_gdrive_connection(self) -> None:
        """
        Set up the `SetupGdriveScreen` screen,
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        if not self.widget_configs_match_saved_configs():
            self.parent_class.mainwindow.show_modal_error_dialog(
                "The values set above must equal the datashuttle settings. "
                "Either press 'Save' or reload this page."
            )
            return

        self.parent_class.mainwindow.push_screen(
            setup_gdrive.SetupGdriveScreen(self.interface)
        )

    def widget_configs_match_saved_configs(self):
        """
        Check that the configs currently stored in the widgets
        on the screen match those stored in the app. This check
        is to avoid user starting to set up a connection with unexpected
        settings. It is a little fiddly as the Input for local
        and central path may or may not contain the project name.
        Therefore, need to check the stored values against
        a version with the project name.
        """
        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        project_name = self.interface.project.cfg.project_name

        for key, value in cfg_kwargs.items():
            saved_val = self.interface.get_configs()[key]
            if key in ["central_path", "local_path"]:
                if value.name != project_name:
                    value = value / project_name
            if saved_val != value:
                return False
        return True

    def setup_configs_for_a_new_project(self) -> None:
        """
        If a project does not exist, we are in NewProjectScreen.
        We need to instantiate a new project based on the project name,
        create configs based on the current widget settings, and display
        any errors to the user, along with confirmation and the
        currently set configs.
        """
        project_name = self.query_one("#configs_name_input").value
        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        interface = Interface()

        success, output = interface.setup_new_project(project_name, cfg_kwargs)

        if success:
            self.interface = interface

            for button_id in [
                "#configs_setup_ssh_connection_button",
                "#configs_setup_aws_connection_button",
                "#configs_setup_gdrive_connection_button",
                "#configs_go_to_project_screen_button",
            ]:
                self.query_one(button_id).visible = False

            # Now show only the Go to Project button and correct connection button
            self.query_one("#configs_go_to_project_screen_button").visible = (
                True
            )

            connection_method = cfg_kwargs["connection_method"]

            # Show only the appropriate setup button
            if connection_method == "ssh":
                self.query_one(
                    "#configs_setup_ssh_connection_button"
                ).visible = True
                setup_message = "Next, setup the SSH connection."
            elif connection_method == "aws":
                self.query_one(
                    "#configs_setup_aws_connection_button"
                ).visible = True
                setup_message = "Next, verify your AWS S3 credentials."
            elif connection_method == "gdrive":
                self.query_one(
                    "#configs_setup_gdrive_connection_button"
                ).visible = True
                setup_message = "Next, verify your Google Drive folder access."
            else:
                setup_message = ""

            if connection_method in ["ssh", "aws", "gdrive"]:
                message = (
                    "A datashuttle project has now been created.\n\n "
                    f"{setup_message} Once complete, navigate to the "
                    "'Main Menu' and proceed to the project page, where you will be "
                    "able to create and transfer project folders."
                )
            else:
                message = (
                    "A datashuttle project has now been created.\n\n "
                    "Next proceed to the project page, where you will be "
                    "able to create and transfer project folders."
                )

            self.parent_class.mainwindow.push_screen(
                modal_dialogs.MessageBox(
                    message,
                    border_color="green",
                ),
            )
        else:
            self.parent_class.mainwindow.show_modal_error_dialog(output)

    def setup_configs_for_an_existing_project(self) -> None:
        """
        If the project already exists, we are on the TabbedContent
        screen. We need to get the configs to set from the current
        widget values and display the set values (or an error if
        there was a problem during setup) to the user.
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        connection_method = self.get_datashuttle_inputs_from_widgets()[
            "connection_method"
        ]

        # Show appropriate setup button based on connection method
        self.query_one("#configs_setup_ssh_connection_button").visible = (
            connection_method == "ssh"
        )
        self.query_one("#configs_setup_aws_connection_button").visible = (
            connection_method == "aws"
        )
        self.query_one("#configs_setup_gdrive_connection_button").visible = (
            connection_method == "gdrive"
        )

        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        success, output = self.interface.set_configs_on_existing_project(
            cfg_kwargs
        )

        if success:
            self.parent_class.mainwindow.push_screen(
                modal_dialogs.MessageBox(
                    "Configs saved.", border_color="green"
                ),
                lambda unused: self.post_message(self.ConfigsSaved()),
            )
        else:
            self.parent_class.mainwindow.show_modal_error_dialog(output)

    def fill_widgets_with_project_configs(self) -> None:
        """
        If a configured project already exists, we want to fill the
        widgets with the current project configs. This in some instances
        requires recasting to a new type of changing the value.

        In the case of the `connection_method` widget, the associated
        connection widgets are hidden / displayed based on the current setting.
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        cfg_to_load = self.interface.get_textual_compatible_project_configs()

        # Local Path
        input = self.query_one("#configs_local_path_input")
        input.value = cfg_to_load["local_path"]

        # Central Path
        input = self.query_one("#configs_central_path_input")
        input.value = (
            cfg_to_load["central_path"] if cfg_to_load["central_path"] else ""
        )

        # Connection Method
        # Make a dict of radiobutton: is on bool to easily find
        # how to set radiobuttons and associated configs
        # fmt: off
        what_radiobuton_is_on = {
            "configs_ssh_radiobutton":
                cfg_to_load["connection_method"] == "ssh",
            "configs_aws_radiobutton":
                cfg_to_load["connection_method"] == "aws",
            "configs_gdrive_radiobutton":
                cfg_to_load["connection_method"] == "gdrive",
            "configs_local_filesystem_radiobutton":
                cfg_to_load["connection_method"] == "local_filesystem",
            "configs_local_only_radiobutton":
                cfg_to_load["connection_method"] is None,
        }
        # fmt: on

        for id, value in what_radiobuton_is_on.items():
            self.query_one(f"#{id}").value = value

        self.switch_connection_widgets_display(
            cfg_to_load["connection_method"]
        )

        # SSH specific fields
        if cfg_to_load["connection_method"] == "ssh":
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

        # AWS specific fields
        elif cfg_to_load["connection_method"] == "aws":
            # AWS Bucket Name
            input = self.query_one("#configs_aws_bucket_name_input")
            value = (
                ""
                if "aws_bucket_name" not in cfg_to_load
                or cfg_to_load["aws_bucket_name"] is None
                else cfg_to_load["aws_bucket_name"]
            )
            input.value = value

            # AWS Region
            input = self.query_one("#configs_aws_region_input")
            value = (
                ""
                if "aws_region" not in cfg_to_load
                or cfg_to_load["aws_region"] is None
                else cfg_to_load["aws_region"]
            )
            input.value = value

        # Google Drive specific fields
        elif cfg_to_load["connection_method"] == "gdrive":
            # Google Drive Folder ID
            input = self.query_one("#configs_gdrive_folder_id_input")
            value = (
                ""
                if "gdrive_folder_id" not in cfg_to_load
                or cfg_to_load["gdrive_folder_id"] is None
                else cfg_to_load["gdrive_folder_id"]
            )
            input.value = value

    def get_datashuttle_inputs_from_widgets(self) -> Dict:
        """
        Get the configs to pass to `make_config_file()` from
        the current TUI settings.
        """
        cfg_kwargs: Dict[str, Any] = {}

        cfg_kwargs["local_path"] = Path(
            self.query_one("#configs_local_path_input").value
        )

        central_path_value = self.query_one(
            "#configs_central_path_input"
        ).value
        if central_path_value == "":
            cfg_kwargs["central_path"] = None
        else:
            cfg_kwargs["central_path"] = Path(central_path_value)

        if self.query_one("#configs_ssh_radiobutton").value:
            connection_method = "ssh"
        elif self.query_one("#configs_aws_radiobutton").value:
            connection_method = "aws"
        elif self.query_one("#configs_gdrive_radiobutton").value:
            connection_method = "gdrive"
        elif self.query_one("#configs_local_filesystem_radiobutton").value:
            connection_method = "local_filesystem"
        elif self.query_one("#configs_local_only_radiobutton").value:
            connection_method = None

        cfg_kwargs["connection_method"] = connection_method

        # Add connection-specific fields based on the selected connection method
        if connection_method == "ssh":
            central_host_id = self.query_one(
                "#configs_central_host_id_input"
            ).value
            cfg_kwargs["central_host_id"] = (
                None if central_host_id == "" else central_host_id
            )

            central_host_username = self.query_one(
                "#configs_central_host_username_input"
            ).value
            cfg_kwargs["central_host_username"] = (
                None if central_host_username == "" else central_host_username
            )

        elif connection_method == "aws":
            aws_bucket_name = self.query_one(
                "#configs_aws_bucket_name_input"
            ).value
            cfg_kwargs["aws_bucket_name"] = (
                None if aws_bucket_name == "" else aws_bucket_name
            )

            aws_region = self.query_one("#configs_aws_region_input").value
            cfg_kwargs["aws_region"] = None if aws_region == "" else aws_region

        elif connection_method == "gdrive":
            gdrive_folder_id = self.query_one(
                "#configs_gdrive_folder_id_input"
            ).value
            cfg_kwargs["gdrive_folder_id"] = (
                None if gdrive_folder_id == "" else gdrive_folder_id
            )

        return cfg_kwargs
