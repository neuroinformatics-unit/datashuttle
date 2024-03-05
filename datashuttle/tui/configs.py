from __future__ import annotations

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
from datashuttle.tui.screens import modal_dialogs, setup_ssh


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

        self.central_input_placeholder_paths = {
            "filesystem": r"C:\path\to\central\my_projects\my_first_project",
            "ssh": r"/nfs/path_on_server/myprojects/central",
        }

    def compose(self) -> ComposeResult:
        """
        `self.config_ssh_widgets` are SSH-setup related widgets
        that are only required when the user selects the SSH
        connection method. These are displayed / hidden based on the
        `connection_method`

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

        config_screen_widgets = [
            Label("Local Path", id="configs_local_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=r"e.g. C:\path\to\local\my_projects\my_first_project",
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
                id="configs_connect_method_radioset",
            ),
            *self.config_ssh_widgets,
            Label("Central Path", id="configs_central_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=f"e.g. {self.central_input_placeholder_paths['filesystem']}",
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
        When we have mounted the widgets, the following logic depends on whether
        we are setting up a new project (`self.project is `None`) or have
        an instantiated project.

        If we have a project, then we want to fill the widgets with the existing
        configs. Otherwise, we set to some reasonable defaults, required to
        determine the display of SSH widgets. "overwrite_files_checkbox"
        should be off by default anyway if `value` is not set, but we set here
        anyway as it is critical this is not on by default.
        """
        if self.interface:
            self.fill_widgets_with_project_configs()
        else:
            self.query_one("#configs_local_filesystem_radiobutton").value = (
                True
            )
            self.switch_ssh_widgets_display(display_bool=False)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        Update the displayed SSH widgets when the `connection_method`
        radiobuttons are changed.
        """
        label = str(event.pressed.label)
        assert label in ["SSH", "Local Filesystem"], "Unexpected label."
        display_bool = True if label == "SSH" else False
        self.switch_ssh_widgets_display(display_bool)

    def switch_ssh_widgets_display(self, display_bool: bool) -> None:
        """
        Show or hide SSH-related configs based on whether the current
        `connection_method` widget is "ssh" or "local_filesystem".

        Parameters
        ----------

        display_bool : bool
            If `True`, display the SSH-related widgets.
        """
        for widget in self.config_ssh_widgets:
            widget.display = display_bool

        self.query_one("#configs_central_path_select_button").disabled = (
            display_bool
        )

        if self.interface is not None:
            self.query_one("#configs_setup_ssh_connection_button").disabled = (
                not display_bool
            )
        else:
            self.query_one("#configs_setup_ssh_connection_button").disabled = (
                True
            )

        if not self.query_one("#configs_central_path_input").value:
            if display_bool:
                placeholder = (
                    f"e.g. {self.central_input_placeholder_paths['ssh']}"
                )
            else:
                placeholder = f"e.g. {self.central_input_placeholder_paths['filesystem']}"
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
                self.setup_configs_for_a_new_project_and_switch_to_tab_screen()
            else:
                self.setup_configs_for_an_existing_project()

        elif event.button.id == "configs_setup_ssh_connection_button":
            self.setup_ssh_connection()

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

        cfg_kwargs = self.get_datashuttle_inputs_from_widgets()

        if any(
            self.interface.get_configs()[key] != value
            for key, value in cfg_kwargs.items()
        ):
            self.parent_class.mainwindow.show_modal_error_dialog(
                "The values set above must equal the datashuttle settings. "
                "Either press 'Save' or reload this page."
            )
            return
        self.parent_class.mainwindow.push_screen(
            setup_ssh.SetupSshScreen(self.interface)
        )

    def setup_configs_for_a_new_project_and_switch_to_tab_screen(self) -> None:
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
            # Could not find a neater way to combine the push screen
            # while initiating the callback in one case but not the other.
            if cfg_kwargs["connection_method"] == "ssh":

                self.query_one(
                    "#configs_setup_ssh_connection_button"
                ).disabled = False
                self.interface = interface

                message = (
                    "A DataShuttle project has now been created.\n\n "
                    "Next, setup the SSH connection. Once complete, navigate to the "
                    "'Main Menu' and proceed to "
                    "the project page, where you will be able to create and "
                    "transfer project folders."
                )

                self.parent_class.mainwindow.push_screen(
                    modal_dialogs.MessageBox(
                        message,
                        border_color="green",
                    ),
                )

            else:
                message = (
                    "A DataShuttle project has now been created.\n\n "
                    "Click 'OK' to proceed to "
                    "the project page, where you will be able to create and "
                    "transfer project folders."
                )
                self.parent_class.mainwindow.push_screen(
                    modal_dialogs.MessageBox(
                        message,
                        border_color="green",
                    ),
                    lambda _: self.parent_class.dismiss(interface),
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

        success, output = self.interface.set_configs_on_existing_project(
            cfg_kwargs
        )

        if success:
            self.parent_class.mainwindow.push_screen(
                modal_dialogs.MessageBox(
                    "Configs saved.", border_color="green"
                )
            )
        else:
            self.parent_class.mainwindow.show_modal_error_dialog(output)

        # Update the DirectoryTree anyway just in case.
        self.post_message(self.ConfigsSaved())

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
        input.value = cfg_to_load["central_path"]

        # Connection Method
        ssh_on = True if cfg_to_load["connection_method"] == "ssh" else False

        radiobutton = self.query_one("#configs_ssh_radiobutton")
        radiobutton.value = ssh_on

        radiobutton = self.query_one("#configs_local_filesystem_radiobutton")
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

    def get_datashuttle_inputs_from_widgets(self) -> Dict:
        """
        Get the configs to pass to `make_config_file()` from
        the current TUI settings.
        """
        cfg_kwargs: Dict[str, Any] = {}

        cfg_kwargs["local_path"] = Path(
            self.query_one("#configs_local_path_input").value
        )

        cfg_kwargs["central_path"] = Path(
            self.query_one("#configs_central_path_input").value
        )

        cfg_kwargs["connection_method"] = (
            "ssh"
            if self.query_one("#configs_ssh_radiobutton").value
            else "local_filesystem"
        )

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

        return cfg_kwargs
