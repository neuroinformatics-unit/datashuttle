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
        `connection_method`.

        `self.config_aws_widgets` are AWS-related widgets.

        `self.config_gdrive_widgets` are Google Drive-related widgets.

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
                placeholder="e.g. my-bucket-name",
                id="configs_aws_bucket_name_input",
            ),
            Label("AWS Region", id="configs_aws_region_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. us-east-1",
                id="configs_aws_region_input",
            ),
        ]

        self.config_gdrive_widgets = [
            Label(
                "Google Drive Folder ID", id="configs_gdrive_folder_id_label"
            ),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="e.g. 1A2B3C4D5E6F7G8H",
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
                id="configs_bottom_buttons_horizontal",
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
        When widgets are mounted, initialize based on whether this is a new
        project or editing an existing one.
        """
        self.query_one("#configs_go_to_project_screen_button").visible = False

        if self.interface:
            self.fill_widgets_with_project_configs()
        else:
            self.query_one("#configs_local_filesystem_radiobutton").value = (
                True
            )
            self.switch_ssh_widgets_display(display_ssh=False)
            self.switch_aws_widgets_display(display_aws=False)
            self.switch_gdrive_widgets_display(display_gdrive=False)
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                False
            )
            self.query_one("#configs_setup_aws_connection_button").visible = (
                False
            )
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = False

        # Setup tooltips
        if not self.interface:
            id = "#configs_name_input"
            self.query_one(id).tooltip = get_tooltip(id)
            assert (
                self.query_one("#configs_local_filesystem_radiobutton").value
                is True
            )
            self.set_central_path_input_tooltip("local_filesystem")
        else:
            method = self.interface.project.cfg["connection_method"]
            self.set_central_path_input_tooltip(method)

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
        Update the displayed widgets and config state when the
        `connection_method` radiobuttons are changed.

        Supports SSH, AWS S3, Google Drive, Local Filesystem, and
        No Connection modes.
        """
        label = str(event.pressed.label)
        assert label in [
            "SSH",
            "AWS S3",
            "Google Drive",
            "Local Filesystem",
            "No connection (local only)",
        ], "Unexpected label."

        is_ssh = label == "SSH"
        is_aws = label == "AWS S3"
        is_gdrive = label == "Google Drive"
        is_local = label == "Local Filesystem"
        is_none = label == "No connection (local only)"

        central_input = self.query_one("#configs_central_path_input")
        select_button = self.query_one("#configs_central_path_select_button")

        # Disable fields if no connection
        if is_none:
            central_input.value = ""
            central_input.disabled = True
            select_button.disabled = True
        else:
            central_input.disabled = False
            select_button.disabled = False

        # Toggle widget groups
        if is_ssh:
            self.switch_ssh_widgets_display(True)
            self.switch_aws_widgets_display(False)
            self.switch_gdrive_widgets_display(False)
        elif is_aws:
            self.switch_ssh_widgets_display(False)
            self.switch_aws_widgets_display(True)
            self.switch_gdrive_widgets_display(False)
        elif is_gdrive:
            self.switch_ssh_widgets_display(False)
            self.switch_aws_widgets_display(False)
            self.switch_gdrive_widgets_display(True)
        else:  # Local Filesystem or No Connection
            self.switch_ssh_widgets_display(False)
            self.switch_aws_widgets_display(False)
            self.switch_gdrive_widgets_display(False)

        # Tooltip update
        if is_ssh:
            self.set_central_path_input_tooltip("ssh")
        elif is_aws:
            self.set_central_path_input_tooltip("aws")
        elif is_gdrive:
            self.set_central_path_input_tooltip("gdrive")
        else:
            self.set_central_path_input_tooltip("local_filesystem")

    def set_central_path_input_tooltip(self, mode: str) -> None:
        """
        Use a different tooltip depending on the selected connection mode.
        `mode` must be one of: 'ssh', 'aws', 'gdrive', 'local_filesystem'
        """
        id = "#configs_central_path_input"
        tooltip_id = {
            "ssh": "config_central_path_input_mode-ssh",
            "aws": "config_central_path_input_mode-aws",
            "gdrive": "config_central_path_input_mode-gdrive",
            "local_filesystem": "config_central_path_input_mode-local_filesystem",
        }.get(mode, "config_central_path_input_mode-local_filesystem")

        self.query_one(id).tooltip = get_tooltip(tooltip_id)

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

    def switch_ssh_widgets_display(self, display_ssh: bool) -> None:
        """
        Show or hide SSH-related configs based on whether the current
        `connection_method` widget is "ssh" or "local_filesystem".

        Parameters
        ----------

        display_ssh : bool
            If `True`, display the SSH-related widgets.
        """
        for widget in self.config_ssh_widgets:
            widget.display = display_ssh

        self.query_one("#configs_central_path_select_button").display = (
            not display_ssh
        )

        if self.interface is None:
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                False
            )
        else:
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                display_ssh
            )

        if not self.query_one("#configs_central_path_input").value:
            if display_ssh:
                placeholder = f"e.g. {self.get_platform_dependent_example_paths('central', ssh=True)}"
            else:
                placeholder = f"e.g. {self.get_platform_dependent_example_paths('central', ssh=False)}"
            self.query_one("#configs_central_path_input").placeholder = (
                placeholder
            )

    def switch_gdrive_widgets_display(self, display_gdrive: bool) -> None:
        """
        Show or hide Google Drive-related configs based on whether the current
        `connection_method` widget is "Google Drive".

        Parameters
        ----------
        display_gdrive : bool
            If `True`, display the Google Drive-related widgets.
        """
        for widget in self.config_gdrive_widgets:
            widget.display = display_gdrive

        # Hide local filesystem selector button when GDrive is selected
        self.query_one("#configs_central_path_select_button").display = (
            not display_gdrive
        )

        # Show or hide GDrive setup button based on interface and mode
        if self.interface is None:
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = False
        else:
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = display_gdrive

        # Set placeholder if empty
        if not self.query_one("#configs_central_path_input").value:
            if display_gdrive:
                placeholder = "e.g. gdrive://project-folder-id"
            else:
                placeholder = f"e.g. {self.get_platform_dependent_example_paths('central', ssh=False)}"
            self.query_one("#configs_central_path_input").placeholder = (
                placeholder
            )

    def switch_aws_widgets_display(self, display_aws: bool) -> None:
        """
        Show or hide AWS S3-related configs based on whether the current
        `connection_method` widget is "AWS S3".

        Parameters
        ----------
        display_aws : bool
            If `True`, display the AWS-related widgets.
        """
        for widget in self.config_aws_widgets:
            widget.display = display_aws

        # Hide local filesystem selector button when AWS is selected
        self.query_one("#configs_central_path_select_button").display = (
            not display_aws
        )

        # Show or hide AWS setup button based on interface and mode
        if self.interface is None:
            self.query_one("#configs_setup_aws_connection_button").visible = (
                False
            )
        else:
            self.query_one("#configs_setup_aws_connection_button").visible = (
                display_aws
            )

        # Set placeholder if empty
        if not self.query_one("#configs_central_path_input").value:
            if display_aws:
                placeholder = "e.g. s3://bucket-name/project-path"
            else:
                placeholder = f"e.g. {self.get_platform_dependent_example_paths('central', ssh=False)}"
            self.query_one("#configs_central_path_input").placeholder = (
                placeholder
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button presses in the configuration screen.
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

    def setup_gdrive_connection(self) -> None:
        """
        Set up the `SetupGdriveScreen` screen.
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

    def setup_aws_connection(self) -> None:
        """
        Set up the `SetupAwsScreen` screen.
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

    def widget_configs_match_saved_configs(self):
        """
        Check that the configs currently stored in the widgets
        on the screen match those stored in the app. This check
        is to avoid user starting to set up SSH with unexpected
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

        Once complete, we dismiss the parent screen (NewProjectScreen),
        returning the new instantiated project. Due to the mainwindow
        `push_screen` callback, this will open the TabbedContent window
        with the new project.
        """
        project_name = self.query_one("#configs_name_input").value
        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        interface = Interface()

        success, output = interface.setup_new_project(project_name, cfg_kwargs)

        if success:

            self.interface = interface

            self.query_one("#configs_go_to_project_screen_button").visible = (
                True
            )

            if cfg_kwargs["connection_method"] == "ssh":

                self.query_one(
                    "#configs_setup_ssh_connection_button"
                ).visible = True
                self.query_one(
                    "#configs_setup_ssh_connection_button"
                ).disabled = False

                message = (
                    "A datashuttle project has now been created.\n\n "
                    "Next, setup the SSH connection. Once complete, navigate to the "
                    "'Main Menu' and proceed to the project page, where you will be "
                    "able to create and transfer project folders."
                )

            elif cfg_kwargs["connection_method"] == "aws":

                self.query_one(
                    "#configs_setup_aws_connection_button"
                ).visible = True
                self.query_one(
                    "#configs_setup_aws_connection_button"
                ).disabled = False

                message = (
                    "A datashuttle project has now been created.\n\n "
                    "Next, setup the AWS connection. Once complete, navigate to the "
                    "'Main Menu' and proceed to the project page, where you will be "
                    "able to create and transfer project folders."
                )

            elif cfg_kwargs["connection_method"] == "gdrive":

                self.query_one(
                    "#configs_setup_gdrive_connection_button"
                ).visible = True
                self.query_one(
                    "#configs_setup_gdrive_connection_button"
                ).disabled = False

                message = (
                    "A datashuttle project has now been created.\n\n "
                    "Next, setup the Google Drive connection. Once complete, navigate to the "
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

        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        # Show relevant setup button depending on selected method
        connection_method = cfg_kwargs.get("connection_method", "")
        if connection_method == "ssh":
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                True
            )
            self.query_one("#configs_setup_aws_connection_button").visible = (
                False
            )
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = False
        elif connection_method == "aws":
            self.query_one("#configs_setup_aws_connection_button").visible = (
                True
            )
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                False
            )
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = False
        elif connection_method == "gdrive":
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = True
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                False
            )
            self.query_one("#configs_setup_aws_connection_button").visible = (
                False
            )
        else:
            self.query_one("#configs_setup_ssh_connection_button").visible = (
                False
            )
            self.query_one("#configs_setup_aws_connection_button").visible = (
                False
            )
            self.query_one(
                "#configs_setup_gdrive_connection_button"
            ).visible = False

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
        "ssh" widgets are hidden / displayed based on the current setting,
        in `self.switch_ssh_widgets_display()`.
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
            "configs_local_filesystem_radiobutton":
                cfg_to_load["connection_method"] == "local_filesystem",
            "configs_local_only_radiobutton":
                cfg_to_load["connection_method"] is None,
            "configs_aws_radiobutton":
                cfg_to_load["connection_method"] == "aws",
            "configs_gdrive_radiobutton":
                cfg_to_load["connection_method"] == "gdrive",
        }
        # fmt: on

        for id, value in what_radiobuton_is_on.items():
            self.query_one(f"#{id}").value = value

        self.switch_ssh_widgets_display(
            display_ssh=what_radiobuton_is_on["configs_ssh_radiobutton"]
        )

        self.switch_aws_widgets_display(
            display_aws=what_radiobuton_is_on["configs_aws_radiobutton"]
        )

        self.switch_gdrive_widgets_display(
            display_gdrive=what_radiobuton_is_on["configs_gdrive_radiobutton"]
        )

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

        # AWS Bucket Name
        input = self.query_one("#configs_aws_bucket_name_input")
        value = (
            ""
            if cfg_to_load.get("aws_bucket_name") is None
            else cfg_to_load["aws_bucket_name"]
        )
        input.value = value

        # AWS Region
        input = self.query_one("#configs_aws_region_input")
        value = (
            ""
            if cfg_to_load.get("aws_region") is None
            else cfg_to_load["aws_region"]
        )
        input.value = value

        # GDrive Folder ID
        input = self.query_one("#configs_gdrive_folder_id_input")
        value = (
            ""
            if cfg_to_load.get("gdrive_folder_id") is None
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

        elif self.query_one("#configs_local_filesystem_radiobutton").value:
            connection_method = "local_filesystem"

        elif self.query_one("#configs_aws_radiobutton").value:
            connection_method = "aws"

        elif self.query_one("#configs_gdrive_radiobutton").value:
            connection_method = "gdrive"

        elif self.query_one("#configs_local_only_radiobutton").value:
            connection_method = None

        cfg_kwargs["connection_method"] = connection_method

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

        aws_bucket_name = self.query_one(
            "#configs_aws_bucket_name_input"
        ).value
        cfg_kwargs["aws_bucket_name"] = (
            None if aws_bucket_name == "" else aws_bucket_name
        )

        aws_region = self.query_one("#configs_aws_region_input").value
        cfg_kwargs["aws_region"] = None if aws_region == "" else aws_region

        gdrive_folder_id = self.query_one(
            "#configs_gdrive_folder_id_input"
        ).value
        cfg_kwargs["gdrive_folder_id"] = (
            None if gdrive_folder_id == "" else gdrive_folder_id
        )

        return cfg_kwargs
