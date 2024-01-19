from rich.text import Text
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Label,
    RadioButton,
    RadioSet,
    Select,
    Switch,
)

from datashuttle.configs import canonical_folders
from datashuttle.tui.custom_widgets import (
    ClickableInput,
    DatatypeCheckboxes,
    TreeAndInputTab,
)
from datashuttle.tui.screens.modal_dialogs import ConfirmScreen
from datashuttle.tui.tabs.transfer_status_tree import TransferStatusTree


class TransferTab(TreeAndInputTab):
    """
    This tb handles the upload / download of files between the local
    and central folders. It contains a TransferDirectoryTree that
    displays the transfer status of the files in the local folder,
    provides functionality to call underlying datashuttle transfer
    functions, and standard TreeAndInputTab and TransferDirectoryTree features.

    Parameters
    ----------

    title : str

    mainwindow : App

    project : DataShuttle
        The initialised datashuttle project to transfer.

    id : str
        The textual widget id.
    """

    def __init__(self, title, mainwindow, project, id=None):
        super(TransferTab, self).__init__(title, id=id)
        self.mainwindow = mainwindow
        self.project = project
        self.prev_click_time = 0.0

    def compose(self):
        self.transfer_all_widgets = [
            Label(
                "All data from: \n\n - Rawdata \n - Derivatives \n\nwill be transferred.",
                id="transfer_all_label",
            )
        ]

        # Fill the select for top-level folder changing, if no top-level
        # folders are found in the project then it will be blank.
        existing_top_level_folders = [
            (folder, folder)
            for folder in canonical_folders.get_top_level_folders()
            if (self.project.get_local_path() / folder).exists()
        ]
        self.transfer_toplevel_widgets = [
            Label(
                "Select top-level folder to transfer.",
                id="transfer_toplevel_label_top",
            ),
            Select(
                existing_top_level_folders,
                value=self.project.get_top_level_folder()
                if any(existing_top_level_folders)
                else Select.BLANK,
                id="transfer_toplevel_select",
                allow_blank=True,
            ),
        ]
        self.transfer_custom_widgets = [
            Label(
                "Select top-level folder to transfer.",
                id="transfer_custom_label_top",
            ),
            Select(
                existing_top_level_folders,
                value=self.project.get_top_level_folder()
                if any(existing_top_level_folders)
                else Select.BLANK,
                id="transfer_custom_select",
                allow_blank=True,
            ),
            Label("Subject(s)"),
            ClickableInput(
                self.mainwindow,
                id="transfer_subject_input",
                placeholder="e.g. sub-001",
            ),
            Label("Session(s)"),
            ClickableInput(
                self.mainwindow,
                id="transfer_session_input",
                placeholder="e.g. ses-001",
            ),
            Label("Datatype(s)"),
            DatatypeCheckboxes(self.project, create_or_transfer="transfer"),
        ]

        yield RadioSet(
            RadioButton("All", id="transfer_all_radiobutton", value=True),
            RadioButton("Top Level", id="transfer_toplevel_radiobutton"),
            RadioButton("Custom", id="transfer_custom_radiobutton"),
            id="transfer_radioset",
        )
        yield TransferStatusTree(
            self.mainwindow,
            self.project,
            id="transfer_directorytree",
        )
        yield Container(
            *self.transfer_all_widgets,
            *self.transfer_toplevel_widgets,
            *self.transfer_custom_widgets,
            id="transfer_params_container",
        )
        yield Horizontal(
            Horizontal(
                Label("Upload"),
                Switch(id="transfer_switch"),
                Label("Download"),
                id="transfer_switch_container",
            ),
            Button("Transfer", id="transfer_transfer_button"),
            Horizontal(),  # push button to left
        )
        yield Label("⭕ Legend", id="transfer_legend")

    def on_mount(self):
        self.query_one(
            "#transfer_params_container"
        ).border_title = "Parameters"
        self.switch_transfer_widgets_display()

        self.query_one("#transfer_legend").tooltip = Text.assemble(
            "Unchanged\n",
            ("Changed\n", "gold3"),
            ("Local Only\n", "green3"),
            # ("Central Only\n", "italic dodger_blue3"),
            ("Error\n", "bright_red"),
        )

    def switch_transfer_widgets_display(self):
        """
        Show or hide transfer parameters based on whether the transfer mode
        currently selected in `transfer_radioset`.
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
        """
        Update the displayed transfer parameter widgets when the
        `transfer_radioset` radiobuttons are changed.
        """
        label = str(event.pressed.label)
        assert label in ["All", "Top Level", "Custom"], "Unexpected label."
        self.switch_transfer_widgets_display()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        If the Transfer button is clicked, opens a modal dialog
        to confirm that the user wishes to transfer their data
        (in the direction selected). If "Yes" is selected,
        `self.transfer_data` (see below) is run.
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

            self.mainwindow.push_screen(
                ConfirmScreen(message), self.transfer_data
            )

    def on_custom_directory_tree_directory_tree_special_key_press(self, event):
        if event.key == "ctrl+r":
            self.reload_directorytree()

        elif event.key in ["ctrl+a", "ctrl+f"]:
            self.handle_fill_input_from_directorytree(
                "#transfer_subject_input", "#transfer_session_input", event
            )

    def reload_directorytree(self):
        self.query_one("#transfer_directorytree").update_transfer_tree()

    def get_top_level_folder_select(self, key):
        assert (
            selected_val := self.query_one(
                key,
            ).value
        ) in canonical_folders.get_top_level_folders()
        return selected_val

    # Transfer data method
    # ----------------------------------------------------------------------------------
    # TODO: everything non-GUI related should be factored to separate module

    def transfer_data(self, transfer_bool: bool) -> None:
        """
        Executes data transfer using the parameters provided
        by the user.

        Parameters
        ----------
        transfer_bool: Passed by `ConfirmScreen`. True if user confirmed
            transfer by clicking "Yes".

        """
        if transfer_bool:
            upload_selected = not self.query_one("#transfer_switch").value

            if self.query_one("#transfer_all_radiobutton").value:
                self.upload_entire_project(upload_selected)

            elif self.query_one("#transfer_toplevel_radiobutton").value:
                self.upload_top_level_only(upload_selected)

            elif self.query_one("#transfer_custom_radiobutton").value:
                self.transfer_custom_selection(upload_selected)

            self.reload_directorytree()

    def transfer_entire_project(self, upload):
        try:
            if upload:
                self.project.upload_entire_project()
            else:
                self.project.download_entire_project()
        except BaseException as e:
            self.mainwindow.show_modal_error_dialog(str(e))
            return

    def upload_top_level_only(self, upload):
        """
        Transfer all files in specified top-level-folder only.

        TODO
        ----
        Currently this implements a  hacky solution to change the project
        top-level folder, do the transfer then change it back.

        It would be better for the transfer function to take top_level_folder
        as an argument that can override the project settings. However, from
        an API level this might be confusing so have changed it yet.
        """
        selected_top_level_folder = self.get_top_level_folder_select(
            "#transfer_toplevel_select"
        )

        temp_top_level_folder = self.project.get_top_level_folder()
        self.project.set_top_level_folder(selected_top_level_folder)
        try:
            if upload:
                self.project.upload_all()
            else:
                self.project.download_all()
        except BaseException as e:
            self.project.set_top_level_folder(temp_top_level_folder)
            self.mainwindow.show_modal_error_dialog(str(e))
            return
        self.project.set_top_level_folder(temp_top_level_folder)

    def transfer_custom_selection(self, upload):
        """
        Tranfser the user-selected subset of the project. Collect the
        sub names, session names and datatypes to transfer, then transfer.

        TODO
        ----
        Currently this implements a  hacky solution to change the project
        top-level folder, do the transfer then change it back.

        It would be better for the transfer function to take top_level_folder
        as an argument that can override the project settings. However, from
        an API level this might be confusing so have changed it yet.
        """
        selected_top_level_folder = self.get_top_level_folder_select(
            "#transfer_custom_select"
        )

        temp_top_level_folder = self.project.get_top_level_folder()
        self.project.set_top_level_folder(selected_top_level_folder)

        sub_names, ses_names, datatype = self.get_sub_ses_names_and_datatype(
            "#transfer_subject_input", "#transfer_session_input"
        )

        try:
            if upload:
                self.project.upload(
                    sub_names=sub_names,
                    ses_names=ses_names,
                    datatype=datatype,
                )
            else:
                self.project.download(
                    sub_names=sub_names,
                    ses_names=ses_names,
                    datatype=datatype,
                )
        except BaseException as e:
            self.project.set_top_level_folder(temp_top_level_folder)
            self.mainwindow.show_modal_error_dialog(str(e))
            return

        self.project.set_top_level_folder(temp_top_level_folder)

    def update_directorytree_root(self, new_root_path):
        """Will automatically refresh the tree"""
        self.query_one("#transfer_directorytree").path = new_root_path
