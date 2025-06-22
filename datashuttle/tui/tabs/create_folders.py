from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.app import TuiApp
    from datashuttle.tui.interface import Interface
    from datashuttle.utils.custom_types import Prefix

from textual import work
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Label,
)

from datashuttle.tui.custom_widgets import (
    ClickableInput,
    CustomDirectoryTree,
    TreeAndInputTab,
)
from datashuttle.tui.screens.create_folder_settings import (
    CreateFoldersSettingsScreen,
)
from datashuttle.tui.screens.datatypes import (
    DatatypeCheckboxes,
    DisplayedDatatypesScreen,
)
from datashuttle.tui.screens.modal_dialogs import (
    SearchingCentralForNextSubSesPopup,
)
from datashuttle.tui.tooltips import get_tooltip
from datashuttle.tui.utils.tui_decorators import (
    ClickInfo,
    require_double_click,
)
from datashuttle.tui.utils.tui_validators import NeuroBlueprintValidator


class CreateFoldersTab(TreeAndInputTab):
    """Create new project files formatted according to the NeuroBlueprint specification."""

    def __init__(self, mainwindow: TuiApp, interface: Interface) -> None:
        """Initialise the CreateFoldersTab.

        Parameters
        ----------
        mainwindow
            The main TUI application.

        interface
            Datashuttle Interface object.

        """
        super(CreateFoldersTab, self).__init__(
            "Create", id="tabscreen_create_tab"
        )
        self.mainwindow = mainwindow
        self.interface = interface
        self.searching_central_popup_widget: (
            SearchingCentralForNextSubSesPopup | None
        ) = None

        self.click_info = ClickInfo()

    def compose(self) -> ComposeResult:
        """Add widgets to the Create Folders tab."""
        yield CustomDirectoryTree(
            self.mainwindow,
            self.interface.get_configs()["local_path"],
            id="create_folders_directorytree",
        )
        yield Label("Subject(s)", id="create_folders_subject_label")
        yield ClickableInput(
            self.mainwindow,
            id="create_folders_subject_input",
            placeholder="e.g. sub-001",
            validate_on=["changed", "submitted"],
            validators=[NeuroBlueprintValidator("sub", self)],
        )
        yield Label("Session(s)", id="create_folders_session_label")
        yield ClickableInput(
            self.mainwindow,
            id="create_folders_session_input",
            placeholder="e.g. ses-001",
            validate_on=["changed", "submitted"],
            validators=[NeuroBlueprintValidator("ses", self)],
        )
        yield Label("Datatype(s)", id="create_folders_datatype_label")
        yield Container(
            DatatypeCheckboxes(
                self.interface, id="create_folders_datatype_checkboxes"
            )
        )
        yield Horizontal(
            Button(
                "Create Folders", id="create_folders_create_folders_button"
            ),
            Horizontal(),
            Button(
                "Displayed Datatypes",
                id="create_folders_displayed_datatypes_button",
            ),
            Button(
                "Settings",
                id="create_folders_settings_button",
            ),
            id="create_folders_buttons_horizontal",
        )

    def on_mount(self) -> None:
        """Handle the widgets immediately after mounting."""
        if not self.interface:
            self.query_one("#configs_name_input").tooltip = get_tooltip(
                "#configs_name_input"
            )

        for id in [
            "#create_folders_directorytree",
            "#create_folders_subject_label",
            "#create_folders_session_label",
            "#create_folders_subject_input",
            "#create_folders_session_input",
            "#create_folders_datatype_label",
        ]:
            self.query_one(id).tooltip = get_tooltip(id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press event.

        The Create Folders button to read out current Input values
        and use these to call project.create_folders().

        `unused_bool` is necessary as dismiss() on the pushed screen
        returns a bool. We use this to trigger revalidation regardless
        of the bool state.
        """
        if event.button.id == "create_folders_create_folders_button":
            self.create_folders()

        elif event.button.id == "create_folders_displayed_datatypes_button":
            self.mainwindow.push_screen(
                DisplayedDatatypesScreen("create", self.interface),
                self.refresh_after_datatypes_changed,
            )

        elif event.button.id == "create_folders_settings_button":
            self.mainwindow.push_screen(
                CreateFoldersSettingsScreen(self.mainwindow, self.interface),
                lambda unused_bool: self.revalidate_inputs(["sub", "ses"]),
            )

    async def refresh_after_datatypes_changed(self, ignore) -> None:
        """Redisplay the datatype checkboxes."""
        await self.recompose()
        self.on_mount()

    @require_double_click
    def on_clickable_input_clicked(
        self, event: ClickableInput.Clicked
    ) -> None:
        """Handle a double click on the custom ClickableInput widget.

        A double click indicates the input should be filled with a suggested value.
        Determine if we have the subject or session input, and
        if it was a left or right click. Then, fill with either
        a generic suggestion or suggestion based on next sub / ses number.
        """
        input_id = event.input.id

        prefix: Prefix = "sub" if "subject" in input_id else "ses"

        if event.ctrl:
            self.fill_input_with_template(prefix, input_id)
        else:
            include_central = self.interface.get_tui_settings()[
                "suggest_next_sub_ses_central"
            ]

            self.suggest_next_sub_ses(prefix, input_id, include_central)

    def on_custom_directory_tree_directory_tree_special_key_press(
        self, event: CustomDirectoryTree.DirectoryTreeSpecialKeyPress
    ) -> None:
        """Handle a key press on the CustomDirectoryTree.

        This can refresh the CustomDirectoryTree or fill / append
        subject/session folder name to the relevant input widget.
        """
        if event.key == "ctrl+r":
            self.reload_directorytree()

        elif event.key in ["ctrl+a", "ctrl+f"]:
            self.handle_fill_input_from_directorytree(
                "#create_folders_subject_input",
                "#create_folders_session_input",
                event,
            )

        elif event.key == "ctrl+n":
            self.mainwindow.prompt_rename_file_or_folder(event.node_path)

    def fill_input_with_template(self, prefix: Prefix, input_id: str) -> None:
        """Fill the sub or ses Input with the name template.

        If `self.templates` is off, then just suggest "sub-" or "ses-".

        Parameters
        ----------
        prefix
            "sub" or "ses"

        input_id
            Textual ID of the Input to fill.

        """
        if self.templates_on(prefix):
            fill_value = self.interface.get_name_templates()[prefix]
        else:
            fill_value = f"{prefix}-"

        input = self.query_one(f"#{input_id}")
        input.value = fill_value

    def templates_on(self, prefix: Prefix) -> bool:
        """Return `True` if the name templates are used in the project."""
        return (
            self.interface.get_name_templates()["on"]
            and self.interface.get_name_templates()[prefix] is not None
        )

    # Validation
    # ----------------------------------------------------------------------------------

    def revalidate_inputs(self, all_prefixes: List[str]) -> None:
        """Revalidate and style both subject and session inputs based on their value."""
        input_names = {
            "sub": "#create_folders_subject_input",
            "ses": "#create_folders_session_input",
        }
        for prefix in all_prefixes:
            key = input_names[prefix]

            value = self.query_one(key).value
            self.query_one(key).validate(value=value)

    def update_input_tooltip(self, message: str, prefix: Prefix) -> None:
        """Update the value of a subject or session tooltip indicating the validation status."""
        id = (
            "#create_folders_subject_input"
            if prefix == "sub"
            else "#create_folders_session_input"
        )
        input = self.query_one(id)
        input.tooltip = message

    # ----------------------------------------------------------------------------------
    # Datashuttle Callers
    # ----------------------------------------------------------------------------------

    # Create Folders
    # ----------------------------------------------------------------------------------

    def create_folders(self) -> None:
        """Create project folders based on the information in TUI widgets."""
        ses_names: Optional[List[str]]

        sub_names, ses_names, datatype = self.get_sub_ses_names_and_datatype(
            "#create_folders_subject_input", "#create_folders_session_input"
        )

        if ses_names == [""]:
            ses_names = None

        success, output = self.interface.create_folders(
            sub_names, ses_names, datatype
        )

        if success:
            self.reload_directorytree()
        else:
            self.mainwindow.show_modal_error_dialog(output)

    def reload_directorytree(self) -> None:
        """Reload the DirectoryTree and also updates validation.

        Notes
        -----
        No longer a good method name due to extended responsibilities
        but done for consistency with other tab refresh methods.

        """
        self.revalidate_inputs(["sub", "ses"])
        self.query_one("#create_folders_directorytree").reload()

    # Filling Inputs
    # ----------------------------------------------------------------------------------

    def suggest_next_sub_ses(
        self, prefix: Prefix, input_id: str, include_central: bool
    ) -> None:
        """Suggests the next sub/ses name for the project.

        Shows a pop up screen in cases when searching for next sub/ses takes
        time such as searching central in SSH connection method.

        Creates an asyncio task which handles the suggestion logic and
        dismissing the pop up.

        Parameters
        ----------
        prefix
            Suggest the next "sub" or "ses".

        input_id
            Textual ID of the widget in which to fill the suggested sub or ses.

        include_central
            If `True`, search central project as well to generate the suggestion.

        """
        assert self.interface.project.cfg["connection_method"] in [
            None,
            "local_filesystem",
            "ssh",
        ]

        if (
            include_central
            and self.interface.project.cfg["connection_method"] == "ssh"
        ):
            self.searching_central_popup_widget = (
                SearchingCentralForNextSubSesPopup(prefix)
            )
            self.mainwindow.push_screen(self.searching_central_popup_widget)

        asyncio.create_task(
            self.fill_suggestion_and_dismiss_popup(
                prefix, input_id, include_central
            ),
            name=f"suggest_next_{prefix}_async_task",
        )

    async def fill_suggestion_and_dismiss_popup(
        self, prefix, input_id, include_central
    ) -> None:
        """Run the `fill_input_with_next_sub_or_ses_template` worker.

        Awaits completion. If an error occurs in  `fill_input_with_next_sub_or_ses_template`,
        it dismisses the popup itself.

        Else, if the worker successfully exits, this function handles dismissal
        of the popup.

        see `suggest_next_sub_ses()` for parameters.
        """
        worker = self.fill_input_with_next_sub_or_ses_template(
            prefix, input_id, include_central
        )
        await worker.wait()
        if self.searching_central_popup_widget:
            self.searching_central_popup_widget.dismiss()
            self.searching_central_popup_widget = None

    @work(exclusive=True, thread=True)
    def fill_input_with_next_sub_or_ses_template(
        self, prefix: Prefix, input_id: str, include_central: bool
    ) -> Worker[None]:
        """Fill an Input the next subject / session in the project (local).

        If `name_templates` are set, then the sub- or ses- first key
        of the template name will be replaced with the suggested
        sub or ses key-value. Otherwise, the sub/ses key-value pair only
        will be suggested.

        It runs in a worker thread as to allow the TUI to show a loading
        animation.

        Parameters
        ----------
        prefix
            Whether to fill the subject or session Input

        input_id
            The textual input name to update.

        include_central
            If `True`, the central project is also validated.

        Returns
        -------
        A textual Worker object for the thread in which the function is run.

        """
        top_level_folder = self.interface.tui_settings[
            "top_level_folder_select"
        ]["create_tab"]

        if prefix == "sub":
            success, output = self.interface.get_next_sub(
                top_level_folder, include_central=include_central
            )
            if not success:
                self.dismiss_popup_and_show_modal_error_dialog_from_thread(
                    output
                )
                return
            else:
                next_val = output
        else:
            sub_names = self.query_one(
                "#create_folders_subject_input"
            ).as_names_list()

            if len(sub_names) > 1:
                self.dismiss_popup_and_show_modal_error_dialog_from_thread(
                    "Can only suggest next session number when a "
                    "single subject is provided."
                )
                return

            if sub_names == [""]:
                self.dismiss_popup_and_show_modal_error_dialog_from_thread(
                    "Must input a subject number before suggesting "
                    "next session number."
                )
                return

            else:
                sub = sub_names[0]

            success, output = self.interface.get_next_ses(
                top_level_folder, sub, include_central=include_central
            )
            if not success:
                self.dismiss_popup_and_show_modal_error_dialog_from_thread(
                    output
                )
                return
            else:
                next_val = output

        if self.templates_on(prefix):
            split_name = self.interface.get_name_templates()[prefix].split("_")
            fill_value = "_".join([next_val, *split_name[1:]])
        else:
            fill_value = next_val

        input = self.query_one(f"#{input_id}")
        input.value = fill_value

    def dismiss_popup_and_show_modal_error_dialog_from_thread(
        self, message: str
    ) -> None:
        """Handle an error while suggesting the next session or subject.

        Called by `fill_input_with_next_sub_or_ses_template`  to display error
        dialog an if an error occurs while suggesting the next sub/ses.
        """
        if self.searching_central_popup_widget:
            self.mainwindow.call_from_thread(
                self.searching_central_popup_widget.dismiss
            )
            self.searching_central_popup_widget = None

        self.mainwindow.show_modal_error_dialog_from_main_thread(message)

    # Validation
    # ----------------------------------------------------------------------------------

    def run_local_validation(self, prefix: Prefix) -> tuple[bool, str]:
        """Run validation of the values stored in the subject / session Inputs.

        First, format the subject name (and session if required)
        which also performs quick name format validations. Then,
        compare the names against all current project sub / names (local)
        and check it is valid. If invalid, the functions will error
        and the error is caught and message returned. Otherwise,
        the formatted name is returned.

        Because validation requires both subject and session
        as input (to check for duplicate sessions within
        subjects) in some cases the 'session' Input will
        show validation error for the subject (i.e. where
        the validation has failed). This is a little ugly
        but subject validation errors will be required to
        fix before dealing with session errors anyway.

        Parameters
        ----------
        prefix
            Whether to run validation on the "sub" or "ses".

        Returns
        -------
        bool
            Indicate whether validation passed successfully.
            If `False`, there was a validation error.
        output
            Str containing the validation error, or successfully formatted name.

        """
        sub_names = self.query_one(
            "#create_folders_subject_input"
        ).as_names_list()

        if prefix == "sub":
            ses_names = None
        else:
            ses_names = self.query_one(
                "#create_folders_session_input"
            ).as_names_list()

        success, output = self.interface.validate_names(
            sub_names,
            ses_names,
        )

        if not success:
            return False, output

        names = (
            output["format_sub"] if prefix == "sub" else output["format_ses"]
        )

        return True, f"Formatted names: {names}"

    def update_directorytree_root(self, new_root_path: Path) -> None:
        """Refresh the tree through the reactive attribute `path`."""
        self.query_one("#create_folders_directorytree").path = new_root_path
