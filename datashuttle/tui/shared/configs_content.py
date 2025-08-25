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
    Select,
    Static,
)

from datashuttle.configs.aws_regions import get_aws_regions_list
from datashuttle.configs.canonical_configs import get_connection_methods_list
from datashuttle.tui.custom_widgets import ClickableInput
from datashuttle.tui.interface import Interface
from datashuttle.tui.screens import (
    modal_dialogs,
    setup_aws,
    setup_gdrive,
    setup_ssh,
)
from datashuttle.tui.tooltips import get_tooltip
from datashuttle.tui.utils import tui_utils


class ConfigsContent(Container):
    """Holds widgets and logic for setting datashuttle configs.

    It is used in `NewProjectPage` to instantiate a new project and
    initialise configs, or in `TabbedContent` to update an existing
    project's configs.

    If no project exists, additional widgets are shown to allow
    entry of a project name for new project initialisation, and
    additional information.

    Otherwise, widgets are filled with the existing projects configs.

    Note:
    ----
    The natural design would be to have two classes (one for a new project,
    one for an existing project) with a shared base class. The issue is that
    for a new project, the screen becomes a set-up project once the config is saved.
    Therefore, because the class mutates from a new-project config to existing-project
    configs, this shared design is used.

    """

    @dataclass
    class ConfigsSaved(Message):
        """An event signalling when the configs are saved."""

        pass

    def __init__(
        self,
        parent_class: Union[ProjectManagerScreen, NewProjectScreen],
        interface: Optional[Interface],
        id: str,
    ) -> None:
        """Initialise the ConfigsContent.

        Parameters
        ----------
        parent_class
            The Screen on which the contents container is mounted.

        interface
            Datashuttle Interface object.

        id
            Textual ID for the configs container.

        """
        super(ConfigsContent, self).__init__(id=id)

        self.parent_class = parent_class
        self.interface = interface
        self.config_ssh_widgets: List[Any] = []

    def compose(self) -> ComposeResult:
        """Set up the Configs widgets.

        `self.config_ssh_widgets` are SSH-setup related widgets
        that are only required when the user selects the SSH
        connection method. These are displayed / hidden based on the
        `connection_method`.

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

        self.config_gdrive_widgets = [
            Label("Root Folder ID", id="configs_gdrive_root_folder_id_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="Google Drive Root Folder ID",
                id="configs_gdrive_root_folder_id_input",
            ),
            Label("Client ID (Optional)", id="configs_gdrive_client_id_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="Google Drive Client ID (Optional)",
                id="configs_gdrive_client_id_input",
            ),
        ]

        self.config_aws_widgets = [
            Label("AWS Access Key ID", id="configs_aws_access_key_id_label"),
            ClickableInput(
                self.parent_class.mainwindow,
                placeholder="AWS Access Key ID eg. EJIBCLSIP2K2PQK3CDON",
                id="configs_aws_access_key_id_input",
            ),
            Label("AWS S3 Region", id="configs_aws_region_label"),
            Select(
                ((region, region) for region in get_aws_regions_list()),
                id="configs_aws_region_select",
            ),
        ]

        config_screen_widgets = [
            Label("Local Path", id="configs_local_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=self.get_platform_dependent_example_paths(
                        "local", "local_filesystem"
                    ),
                    id="configs_local_path_input",
                ),
                Button("Select", id="configs_local_path_select_button"),
                id="configs_local_path_button_input_container",
            ),
            Label("Connection Method", id="configs_connect_method_label"),
            RadioSet(
                RadioButton(
                    "No connection (local only)",
                    id="configs_local_only_radiobutton",
                ),
                RadioButton(
                    "Local Filesystem",
                    id=self.radiobutton_id_from_connection_method(
                        "local_filesystem"
                    ),
                ),
                RadioButton(
                    "SSH", id=self.radiobutton_id_from_connection_method("ssh")
                ),
                RadioButton(
                    "Google Drive",
                    id=self.radiobutton_id_from_connection_method("gdrive"),
                ),
                RadioButton(
                    "AWS S3",
                    id=self.radiobutton_id_from_connection_method("aws"),
                ),
                id="configs_connect_method_radioset",
            ),
            *self.config_ssh_widgets,
            *self.config_gdrive_widgets,
            *self.config_aws_widgets,
            Label("Central Path", id="configs_central_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=self.get_platform_dependent_example_paths(
                        "central", "local_filesystem"
                    ),
                    id="configs_central_path_input",
                ),
                Button("Select", id="configs_central_path_select_button"),
                id="configs_central_path_button_input_container",
            ),
            Horizontal(
                Button("Save", id="configs_save_configs_button"),
                Horizontal(
                    Button(
                        "Setup Button",
                        id="configs_setup_connection_button",
                    ),
                    id="setup_buttons_container",
                ),
                # Below button is always hidden when accessing
                # configs from project manager screen
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
        """Handle logic immediately following widget mounting.

        When we have mounted the widgets, the following logic depends on whether
        we are setting up a new project (`self.project is `None`) or have
        an instantiated project.

        If we have a project, then we want to fill the widgets with the existing
        configs. Otherwise, we set to some reasonable defaults, required to
        determine the display of SSH widgets. "overwrite_files_checkbox"
        should be off by default anyway if `value` is not set, but we set here
        anyway as it is critical this is not on by default.
        """
        # Setup display widget defaults
        self.query_one("#configs_go_to_project_screen_button").visible = False
        if self.interface:
            self.fill_widgets_with_project_configs()
            self.setup_widgets_to_display(
                connection_method=self.interface.get_configs()[
                    "connection_method"
                ]
            )
        else:
            self.query_one(
                "#configs_local_filesystem_radiobutton"
            ).value = True

            self.setup_widgets_to_display(connection_method="local_filesystem")

        # Setup tooltips
        if not self.interface:
            id = "#configs_name_input"
            self.query_one(id).tooltip = get_tooltip(id)

            # Assumes 'local_filesystem' is default if no project set.
            assert (
                self.query_one("#configs_local_filesystem_radiobutton").value
                is True
            )

        for id in [
            "#configs_local_path_input",
            "#configs_connect_method_label",
            "#configs_local_filesystem_radiobutton",
            "#configs_ssh_radiobutton",
            "#configs_local_only_radiobutton",
            "#configs_central_host_username_input",
            "#configs_central_host_id_input",
            "#configs_gdrive_client_id_input",
            "#configs_gdrive_root_folder_id_input",
        ]:
            self.query_one(id).tooltip = get_tooltip(id)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Update the SSH widgets when the `connection_method` radiobuttons are changed.

        When SSH is set, ssh config-setters are shown. Otherwise, these
        are hidden.

        When mode is `No connection`, the `central_path` is cleared and
        disabled.
        """
        label = str(event.pressed.label)
        radiobutton_id = event.pressed.id

        assert label in [
            "SSH",
            "Local Filesystem",
            "No connection (local only)",
            "Google Drive",
            "AWS S3",
        ], "Unexpected label."

        connection_method = self.connection_method_from_radiobutton_id(
            radiobutton_id
        )

        self.setup_widgets_to_display(connection_method)

        self.set_central_path_input_tooltip(connection_method)

    def radiobutton_id_from_connection_method(
        self, connection_method: str
    ) -> str:
        """Create a canonical radiobutton textual ID from the connection method."""
        return f"configs_{connection_method}_radiobutton"

    def connection_method_from_radiobutton_id(
        self, radiobutton_id: str
    ) -> str | None:
        """Convert back from radiobutton Textual ID to connection method."""
        assert radiobutton_id.startswith("configs_")
        assert radiobutton_id.endswith("_radiobutton")

        connection_string = radiobutton_id[
            len("configs_") : -len("_radiobutton")
        ]
        return (
            connection_string
            if connection_string in get_connection_methods_list()
            else None
        )

    def set_central_path_input_tooltip(
        self, connection_method: str | None
    ) -> None:
        """Set tooltip depending on whether connection method is SSH or local filesystem."""
        if connection_method is None:
            tooltip = get_tooltip(
                "config_central_path_input_mode-local_filesystem"
            )
        else:
            tooltip = get_tooltip(
                f"config_central_path_input_mode-{connection_method}"
            )
        self.query_one("#configs_central_path_input").tooltip = tooltip

    def get_platform_dependent_example_paths(
        self,
        local_or_central: Literal["local", "central"],
        connection_method: str,
    ) -> str:
        """Get example paths for the local or central Inputs depending on operating system.

        Parameters
        ----------
        local_or_central
            The "local" or "central" input to fill.

        connection_method
            Connection method e.g. "local_filesystem"

        """
        assert local_or_central in ["local", "central"]

        # Handle the ssh central case separately
        # because it is always the same
        if (
            local_or_central == "central"
            and connection_method != "local_filesystem"
        ):
            if connection_method == "ssh":
                example_path = "e.g. /nfs/path_on_server/myprojects/central"
            elif connection_method in ["aws", "gdrive"]:
                example_path = ""

        else:
            if platform.system() == "Windows":
                example_path = rf"e.g. C:\path\to\{local_or_central}\my_projects\my_first_project"
            else:
                example_path = f"e.g. /path/to/{local_or_central}/my_projects/my_first_project"

        return example_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press event.

        Enables the Create Folders button to read out current input
        values and use these to call project.create_folders().
        """
        if event.button.id == "configs_save_configs_button":
            if not self.interface:
                self.setup_configs_for_a_new_project()
            else:
                self.setup_configs_for_an_existing_project()

        elif event.button.id == "configs_setup_connection_button":
            assert self.interface is not None, (
                "type narrow flexible `interface`"
            )

            connection_method = self.interface.get_configs()[
                "connection_method"
            ]

            if not self.widget_configs_match_saved_configs():
                self.parent_class.mainwindow.show_modal_error_dialog(
                    "The values set above must equal the datashuttle settings. "
                    "Either press 'Save' or reload this page."
                )
                return

            if connection_method == "ssh":
                self.setup_ssh_connection()
            elif connection_method == "gdrive":
                self.setup_gdrive_connection()
            elif connection_method == "aws":
                self.setup_aws_connection()

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
        """Update the `local` or `central` Inputs after `SelectDirectoryTreeScreen` returns a path.

        Parameters
        ----------
        path_
            The path returned from `SelectDirectoryTreeScreen`. If `False`,
            the screen exited with no directory selected.

        local_or_central
            The Input to fill with the path.

        """
        if path_ is False:
            return

        if local_or_central == "local":
            self.query_one(
                "#configs_local_path_input"
            ).value = path_.as_posix()
        elif local_or_central == "central":
            self.query_one(
                "#configs_central_path_input"
            ).value = path_.as_posix()

    def setup_ssh_connection(self) -> None:
        """Run the SSH set up in a new screen."""
        assert self.interface is not None, "type narrow flexible `interface`"

        self.parent_class.mainwindow.push_screen(
            setup_ssh.SetupSshScreen(self.interface)
        )

    def setup_gdrive_connection(self) -> None:
        """Run the Google Drive set up in a new screen."""
        assert self.interface is not None, "type narrow flexible `interface`"

        self.parent_class.mainwindow.push_screen(
            setup_gdrive.SetupGdriveScreen(self.interface)
        )

    def setup_aws_connection(self) -> None:
        """Run the AWS set up in a new screen."""
        assert self.interface is not None, "type narrow flexible `interface`"

        self.parent_class.mainwindow.push_screen(
            setup_aws.SetupAwsScreen(self.interface)
        )

    def widget_configs_match_saved_configs(self):
        """Ensure configs as set on screen match those stored in the project object.

        This check is to avoid user starting to set up SSH with unexpected
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
                if value is not None and value.name != project_name:
                    value = value / project_name
            if saved_val != value:
                return False
        return True

    def setup_configs_for_a_new_project(self) -> None:
        """Set up configs when the project does not exist.

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

            self.query_one(
                "#configs_go_to_project_screen_button"
            ).visible = True

            # A message template to display custom message to user according to the chosen connection method
            message_template = tui_utils.get_project_created_message_template()

            # Could not find a neater way to combine the push screen
            # while initiating the callback in one case but not the other.
            connection_method = cfg_kwargs["connection_method"]

            # To trigger the appearance of "Setup connection" button
            self.setup_widgets_to_display(connection_method)

            if connection_method == "ssh":
                message = message_template.format(method_name="SSH")

            elif connection_method == "gdrive":
                message = message_template.format(method_name="Google Drive")

            elif connection_method == "aws":
                message = message_template.format(method_name="AWS")

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
        """Set up configs when the project already exists.

        If the project already exists, we are on the TabbedContent
        screen. We need to get the configs to set from the current
        widget values and display the set values (or an error if
        there was a problem during setup) to the user.
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        # Handle the edge case where connection method is changed after
        # saving on the 'Make New Project' screen.

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
            # To trigger the appearance of "Setup connection" button
            self.setup_widgets_to_display(cfg_kwargs["connection_method"])
        else:
            self.parent_class.mainwindow.show_modal_error_dialog(output)

    def fill_widgets_with_project_configs(self) -> None:
        """Fill widgets on screen with content from the project config file.

        If a configured project already exists, we want to fill the
        widgets with the current project configs. This in some instances
        requires recasting to a new type of changing the value.

        In the case of the `connection_method` widget, the associated connection
        method radio button is hidden / displayed based on the current settings.
        This change of radio button triggers `on_radio_set_changed` which displays
        the appropriate connection method widgets.
        """
        assert self.interface is not None, "type narrow flexible `interface`"

        cfg_to_load = self.interface.get_textual_compatible_project_configs()

        # Connection Method
        # Make a dict of radiobutton: is on bool to easily find
        # how to set radiobuttons and associated configs
        # fmt: off
        what_radiobuton_is_on = {
            "configs_ssh_radiobutton":
                cfg_to_load["connection_method"] == "ssh",
            "configs_local_filesystem_radiobutton":
                cfg_to_load["connection_method"] == "local_filesystem",
            "configs_gdrive_radiobutton":
                cfg_to_load["connection_method"] == "gdrive",
            "configs_aws_radiobutton":
                cfg_to_load["connection_method"] == "aws",
            "configs_local_only_radiobutton":
                cfg_to_load["connection_method"] is None,
        }
        # fmt: on

        for id, value in what_radiobuton_is_on.items():
            self.query_one(f"#{id}").value = value

        self.fill_inputs_with_project_configs()

    def fill_inputs_with_project_configs(self) -> None:
        """Fill the input widgets with the current project configs.

        It is used while setting up widgets for the project while mounting the current tab.
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

        # Google Drive Client ID
        input = self.query_one("#configs_gdrive_client_id_input")
        value = (
            ""
            if cfg_to_load["gdrive_client_id"] is None
            else cfg_to_load["gdrive_client_id"]
        )
        input.value = value

        # Google Drive Root Folder ID
        input = self.query_one("#configs_gdrive_root_folder_id_input")
        value = (
            ""
            if cfg_to_load["gdrive_root_folder_id"] is None
            else cfg_to_load["gdrive_root_folder_id"]
        )
        input.value = value

        # AWS Access Key ID
        input = self.query_one("#configs_aws_access_key_id_input")
        value = (
            ""
            if cfg_to_load["aws_access_key_id"] is None
            else cfg_to_load["aws_access_key_id"]
        )
        input.value = value

        # AWS S3 Region
        select = self.query_one("#configs_aws_region_select")
        value = (
            Select.BLANK
            if cfg_to_load["aws_region"] is None
            else cfg_to_load["aws_region"]
        )
        select.value = value

    def setup_widgets_to_display(self, connection_method: str | None) -> None:
        """Set up widgets to display based on the chosen `connection_method` on the radiobutton.

        The widgets pertaining to the chosen connection method will be displayed.
        This is done by dedicated functions for each connection method
        which display widgets on receiving a `True` flag.

        Also, this function handles other TUI changes like displaying "setup connection"
        button, disabling central path input in a local only project, etc.

        Called on mount, on radiobuttons' switch and upon saving project configs.
        """
        if connection_method:
            assert connection_method in get_connection_methods_list(), (
                "Unexpected Connection Method"
            )

        # Connection specific widgets
        connection_widget_display_functions = {
            "ssh": self.config_ssh_widgets,
            "gdrive": self.config_gdrive_widgets,
            "aws": self.config_aws_widgets,
        }

        for (
            name,
            connection_widgets,
        ) in connection_widget_display_functions.items():
            for widget in connection_widgets:
                widget.display = connection_method == name

        has_connection_method = connection_method is not None

        # Central Path Input
        self.query_one(
            "#configs_central_path_input"
        ).disabled = not has_connection_method
        self.query_one(
            "#configs_central_path_select_button"
        ).disabled = not has_connection_method

        # Central Path Input Placeholder
        if connection_method is None:
            self.query_one("#configs_central_path_input").value = ""
            self.query_one("#configs_central_path_input").placeholder = ""
        else:
            placeholder = self.get_platform_dependent_example_paths(
                "central",
                connection_method,
            )
            self.query_one(
                "#configs_central_path_input"
            ).placeholder = placeholder

        # Central Path Label
        central_path_label = self.query_one("#configs_central_path_label")
        if connection_method in ["gdrive", "aws"]:
            central_path_label.update(content="Central Path (Optional)")
        else:
            central_path_label.update(content="Central Path")

        # Central Path Select Button
        show_central_path_select = connection_method not in [
            "ssh",
            "aws",
            "gdrive",
        ]
        self.query_one(
            "#configs_central_path_select_button"
        ).display = show_central_path_select

        # fmt: off
        # Setup connection button
        setup_connection_button = self.query_one(
            "#configs_setup_connection_button"
        )

        if (
            not connection_method
            or connection_method == "local_filesystem"
            or not self.interface
            or connection_method != self.interface.get_configs()["connection_method"]
        ):
            setup_connection_button.visible = False
        # fmt: on
        else:
            setup_connection_button.visible = True

            if connection_method == "ssh":
                setup_connection_button.label = "Setup SSH Connection"
            elif connection_method == "gdrive":
                setup_connection_button.label = "Setup Google Drive Connection"
            elif connection_method == "aws":
                setup_connection_button.label = "Setup AWS Connection"

    def get_datashuttle_inputs_from_widgets(self) -> Dict:
        """Get the configs to pass to `make_config_file()` from the current TUI settings."""
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

        for id in [
            "configs_local_filesystem_radiobutton",
            "configs_ssh_radiobutton",
            "configs_gdrive_radiobutton",
            "configs_aws_radiobutton",
            "configs_local_only_radiobutton",
        ]:
            if self.query_one("#" + id).value:
                connection_method = self.connection_method_from_radiobutton_id(
                    id
                )
                break

        cfg_kwargs["connection_method"] = connection_method

        # SSH specific
        if connection_method == "ssh":
            cfg_kwargs["central_host_id"] = (
                self.get_config_value_from_input_value(
                    "#configs_central_host_id_input"
                )
            )

            cfg_kwargs["central_host_username"] = (
                self.get_config_value_from_input_value(
                    "#configs_central_host_username_input"
                )
            )

        # Google Drive specific
        elif connection_method == "gdrive":
            cfg_kwargs["gdrive_client_id"] = (
                self.get_config_value_from_input_value(
                    "#configs_gdrive_client_id_input"
                )
            )

            cfg_kwargs["gdrive_root_folder_id"] = (
                self.get_config_value_from_input_value(
                    "#configs_gdrive_root_folder_id_input"
                )
            )

        # AWS specific
        elif connection_method == "aws":
            cfg_kwargs["aws_access_key_id"] = (
                self.get_config_value_from_input_value(
                    "#configs_aws_access_key_id_input"
                )
            )

            aws_region = self.query_one("#configs_aws_region_select").value
            cfg_kwargs["aws_region"] = (
                None if aws_region == Select.BLANK else aws_region
            )

        return cfg_kwargs

    def get_config_value_from_input_value(
        self, input_box_selector: str
    ) -> str | None:
        """Format the Input value from string to string or `None`."""
        input_value = self.query_one(input_box_selector).value

        return None if input_value == "" else input_value
