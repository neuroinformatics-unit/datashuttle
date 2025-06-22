from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult
    from textual.worker import Worker

    from datashuttle.tui.app import TuiApp
    from datashuttle.tui.custom_widgets import CustomDirectoryTree
    from datashuttle.tui.interface import Interface
    from datashuttle.utils.custom_types import InterfaceOutput

from rich.text import Text
from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Label,
    RadioButton,
    RadioSet,
    Select,
    Switch,
)

from datashuttle.tui.custom_widgets import (
    ClickableInput,
    TopLevelFolderSelect,
    TreeAndInputTab,
)
from datashuttle.tui.screens.datatypes import (
    DatatypeCheckboxes,
    DisplayedDatatypesScreen,
)
from datashuttle.tui.screens.modal_dialogs import (
    ConfirmAndAwaitTransferPopup,
)
from datashuttle.tui.tabs.transfer_status_tree import TransferStatusTree
from datashuttle.tui.tooltips import get_tooltip


class TransferTab(TreeAndInputTab):
    """The Project Manager's Transfer tab.

    Handles the upload / download of files between local
    and central folders. It contains a TransferDirectoryTree that
    displays the transfer status of the files in the local folder,
    and calls underlying datashuttle transfer functions.
    """

    def __init__(
        self,
        title: str,
        mainwindow: TuiApp,
        interface: Interface,
        id: Optional[str] = None,
    ) -> None:
        """Initialise the TransferTab.

        Parameters
        ----------
        title
            The title of the tab

        mainwindow
            The main TUI app

        interface
            TUI-datashuttle interface object

        id
            The textual widget id.

        Attributes
        ----------
        show_legend
            Convenience attribute linked to a global setting exists that
            turns off / on styling of DirectoryTree nodes based on transfer status. `

            `self.mainwindow.load_global_settings()[
                "show_transfer_tree_status"
            ]`
            When on, the legend must be hidden.

        """
        super(TransferTab, self).__init__(title, id=id)
        self.mainwindow = mainwindow
        self.interface = interface
        self.prev_click_time = 0.0
        self.show_legend = self.mainwindow.load_global_settings()[
            "show_transfer_tree_status"
        ]

    # Setup
    # ----------------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Set the widgets on the Transfer Tab."""
        self.transfer_all_widgets = [
            Label(
                "All data from: \n\n - Rawdata \n - Derivatives \n\nwill be transferred.",
                id="transfer_all_label",
            )
        ]

        # Fill the select for top-level folder changing, if no top-level
        # folders are found in the project then it will be blank.
        self.transfer_toplevel_widgets = [
            Label(
                "Select top-level folder to transfer.",
                id="transfer_toplevel_label_top",
            ),
            TopLevelFolderSelect(
                self.interface,
                id="transfer_toplevel_select",
            ),
        ]
        self.transfer_custom_widgets = [
            Label(
                "Select top-level folder to transfer.",
                id="transfer_custom_label_top",
            ),
            TopLevelFolderSelect(
                self.interface,
                id="transfer_custom_select",
            ),
            Label("Subject(s)", id="transfer_subject_label"),
            ClickableInput(
                self.mainwindow,
                id="transfer_subject_input",
                placeholder="e.g. sub-001",
            ),
            Label("Session(s)", id="transfer_session_label"),
            ClickableInput(
                self.mainwindow,
                id="transfer_session_input",
                placeholder="e.g. ses-001",
            ),
            # These are almost identical to create tab
            Label("Datatype(s)", id="transfer_datatype_label"),
            DatatypeCheckboxes(
                self.interface,
                create_or_transfer="transfer",
                id="transfer_custom_datatype_checkboxes",
            ),
            Button(
                "Displayed Datatypes",
                id="transfer_tab_displayed_datatypes_button",
            ),
        ]

        yield TransferStatusTree(
            self.mainwindow,
            self.interface,
            id="transfer_directorytree",
        )
        yield RadioSet(
            RadioButton("All", id="transfer_all_radiobutton", value=True),
            RadioButton("Top Level", id="transfer_toplevel_radiobutton"),
            RadioButton("Custom", id="transfer_custom_radiobutton"),
            id="transfer_radioset",
        )
        yield Container(
            *self.transfer_all_widgets,
            *self.transfer_toplevel_widgets,
            *self.transfer_custom_widgets,
            id="transfer_params_container",
        )
        yield Horizontal(
            Vertical(
                Button("Transfer", id="transfer_transfer_button"),
                Horizontal(
                    Label("Upload", id="transfer_switch_upload_label"),
                    Switch(id="transfer_switch"),
                    Label("Download", id="transfer_switch_download_label"),
                    id="transfer_switch_container",
                ),
            ),
            Vertical(
                Horizontal(
                    Label("Overwrite:", id="transfer_tab_overwrite_label"),
                    Select(
                        (
                            (name, name)
                            for name in ["Never", "Always", "If Source Newer"]
                        ),
                        value=self.interface.tui_settings[
                            "overwrite_existing_files"
                        ]
                        .title()
                        .replace("_", " "),
                        allow_blank=False,
                        id="transfer_tab_overwrite_select",
                    ),
                ),
                # needs to be in horizontal or formats with large space for some reason.
                Horizontal(
                    Checkbox(
                        "Dry Run",
                        value=self.interface.tui_settings["dry_run"],
                        id="transfer_tab_dry_run_checkbox",
                    )
                ),
            ),
            id="transfer_tab_transfer_settings_container",
        )

        if self.show_legend:
            yield Label("⭕ Legend", id="transfer_legend")

    def on_mount(self) -> None:
        """Update the widgets immediately after mounting."""
        for id in [
            "#transfer_directorytree",
            "#transfer_switch_container",
            "#transfer_subject_input",
            "#transfer_session_input",
            "#transfer_all_checkbox",
            "#transfer_all_datatype_checkbox",
            "#transfer_all_non_datatype_checkbox",
            "#transfer_tab_overwrite_select",
            "#transfer_tab_dry_run_checkbox",
        ]:
            from textual.css.query import NoMatches

            try:
                # if checkbox is removed by user, hard to predict, skip.
                self.query_one(id).tooltip = get_tooltip(id)
            except NoMatches:
                pass

        self.switch_transfer_widgets_display()

        if self.show_legend:
            self.query_one("#transfer_legend").tooltip = Text.assemble(
                "Unchanged\n",
                ("Changed\n", "gold3"),
                ("Local Only\n", "green3"),
                # ("Central Only\n", "italic dodger_blue3"),
                ("Error\n", "bright_red"),
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle a Select widget changed on the tab."""
        if event.select.id == "transfer_tab_overwrite_select":
            assert event.select.value in ["Never", "Always", "If Source Newer"]
            format_select = event.select.value.lower().replace(" ", "_")
            self.interface.save_tui_settings(
                format_select,
                "overwrite_existing_files",
            )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle a Checkbox widget changed on the tab."""
        if event.checkbox.id == "transfer_tab_dry_run_checkbox":
            self.interface.save_tui_settings(
                event.checkbox.value,
                "dry_run",
            )

    # Manage Widgets
    # ----------------------------------------------------------------------------------

    def switch_transfer_widgets_display(self) -> None:
        """Show or hide transfer parameters based on whether the transfer mode.

        The transfer mode is selected by the radiobutton e.g. Custom.
        """
        for widget in self.transfer_all_widgets:
            widget.display = self.query_one("#transfer_all_radiobutton").value

        for widget in self.transfer_toplevel_widgets:
            widget.display = self.query_one(
                "#transfer_toplevel_radiobutton"
            ).value

        for widget in self.transfer_custom_widgets:
            widget.display = self.query_one(
                "#transfer_custom_radiobutton"
            ).value

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Update the transfer parameter widgets when the `transfer_radioset` are changed."""
        label = str(event.pressed.label)
        assert label in ["All", "Top Level", "Custom"], "Unexpected label."
        self.switch_transfer_widgets_display()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press on a tab.

        If the Transfer button is clicked, opens a modal dialog
        to confirm that the user wishes to transfer their data
        (in the direction selected). If "Yes" is selected,
        `self.transfer_data` (see below) is run.

        And `ConfirmAndAwaitTransferPopup` handles the UI updates.
        """
        if event.button.id == "transfer_transfer_button":
            if not self.query_one("#transfer_switch").value:
                direction = "upload"
                preposition = "to"
            else:
                direction = "download"
                preposition = "from"

            message = Text.assemble(
                "You are about to ",
                (f"{direction}", "chartreuse3 underline"),
                f" the selected project data {preposition} \nthe project's configured",
                " central filesystem.\n\nAre you sure you wish to proceed?\n",
            )

            finish_transfer_screen = ConfirmAndAwaitTransferPopup(
                message, self.transfer_data
            )
            self.mainwindow.push_screen(finish_transfer_screen)

        if event.button.id == "transfer_tab_displayed_datatypes_button":
            self.mainwindow.push_screen(
                DisplayedDatatypesScreen("transfer", self.interface),
                self.refresh_after_datatype_changed,
            )

    async def refresh_after_datatype_changed(self, ignore):
        """Refresh Checkboxes after the shown datatypes have changed."""
        await self.recompose()
        self.on_mount()
        self.query_one("#transfer_custom_radiobutton").value = True
        self.switch_transfer_widgets_display()

    def on_custom_directory_tree_directory_tree_special_key_press(
        self, event: CustomDirectoryTree.DirectoryTreeSpecialKeyPress
    ) -> None:
        """Handle a key press on the CustomDirectoryTree."""
        if event.key == "ctrl+r":
            self.reload_directorytree()

        elif event.key in ["ctrl+a", "ctrl+f"]:
            self.handle_fill_input_from_directorytree(
                "#transfer_subject_input", "#transfer_session_input", event
            )

        elif event.key == "ctrl+n":
            self.mainwindow.prompt_rename_file_or_folder(event.node_path)
            self.reload_directorytree()

    def reload_directorytree(self) -> None:
        """Refresh the CustomDirectoryTree."""
        self.query_one("#transfer_directorytree").update_transfer_tree()

    def update_directorytree_root(self, new_root_path: Path) -> None:
        """Automatically refresh the tree through the reactive variable `path`."""
        self.query_one("#transfer_directorytree").path = new_root_path

    # Transfer
    # ----------------------------------------------------------------------------------

    @work(exclusive=True, thread=True)
    def transfer_data(self) -> Worker[InterfaceOutput]:
        """Transfer data in a threaded worker.

        This function transfers data based on the config provided by the radio buttons
        such as a) the data to be transferred (all / top-level-folders / custom) b) the
        direction of transfer c) overwrite rules, etc.

        This function is passed to `ConfirmAndAwaitTransferPopup` which calls it to handle
        data transfer in a worker thread. The UI updates during and after transfer are
        handled by `ConfirmAndAwaitTransferPopup`.

        Returns
        -------
        An InterfaceOutput object that indicates whether the transfer was a success.
        Wrapped in an awaitable Textual Worker for the thread in the function is run.

        """
        upload = not self.query_one("#transfer_switch").value

        if self.query_one("#transfer_all_radiobutton").value:
            success, output = self.interface.transfer_entire_project(upload)

        elif self.query_one("#transfer_toplevel_radiobutton").value:
            selected_top_level_folder = self.query_one(
                "#transfer_toplevel_select"
            ).get_top_level_folder()

            success, output = self.interface.transfer_top_level_only(
                selected_top_level_folder, upload
            )

        elif self.query_one("#transfer_custom_radiobutton").value:
            selected_top_level_folder = self.query_one(
                "#transfer_custom_select"
            ).get_top_level_folder()

            sub_names, ses_names, datatype = (
                self.get_sub_ses_names_and_datatype(
                    "#transfer_subject_input", "#transfer_session_input"
                )
            )
            success, output = self.interface.transfer_custom_selection(
                selected_top_level_folder,
                sub_names,
                ses_names,
                datatype,
                upload,
            )

        self.app.call_from_thread(self.reload_directorytree)

        return success, output
