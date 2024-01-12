from os import walk
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Select,
    Switch,
    TabPane,
)
from textual.widgets._directory_tree import DirectoryTree, DirEntry
from textual.widgets._tree import TOGGLE_STYLE, TreeNode

from datashuttle.configs import canonical_folders
from datashuttle.configs.canonical_configs import get_datatypes
from datashuttle.tui.custom_widgets import DatatypeCheckboxes
from datashuttle.tui.screens.modal_dialogs import ConfirmScreen
from datashuttle.tui.utils.tui_decorators import require_double_click
from datashuttle.utils.rclone import get_local_and_central_file_differences


class TransferTab(TabPane):
    def __init__(self, mainwindow, project):
        super(TransferTab, self).__init__(
            "Transfer", id="tabscreen_transfer_tab"
        )
        self.mainwindow = mainwindow
        self.project = project

        self.prev_click_time = 0.0

    def compose(self):
        self.transfer_all_widgets = [
            Label(
                "All data from: \n\n - Rawdata \n - Derivatives \n\nWill be transferred."
                " Existing data with \nthe same file details on central will not be \noverwritten "
                "by default",
                id="transfer_all_label",
            )
        ]

        self.transfer_toplevel_widgets = [
            Label(
                "Select top-level folder to transfer.",
                id="transfer_toplevel_label_top",
            ),
            Select(
                [
                    (folder, folder)
                    for folder in canonical_folders.get_top_level_folders()
                    if (self.project.get_local_path() / folder).exists()
                ],
                value=self.project.get_top_level_folder(),
                id="transfer_toplevel_select",
                allow_blank=False,
            ),
            Label(
                "Existing data with the same file details on \ncentral will not be overwritten by default."
            ),
        ]

        self.transfer_custom_widgets = [
            Label("Subject(s)"),
            Input(
                id="transfer_subject_input",
                placeholder="e.g. sub-001",
            ),
            Label("Session(s)"),
            Input(
                id="transfer_session_input",
                placeholder="e.g. ses-001",
            ),
            Label("Datatype(s)"),
            DatatypeCheckboxes(self.project, transfer_checkboxes=True),
        ]

        yield RadioSet(
            RadioButton("All", id="transfer_all_radiobutton", value=True),
            RadioButton("Top Level", id="transfer_toplevel_radiobutton"),
            RadioButton("Custom", id="transfer_custom_radiobutton"),
            id="transfer_radioset",
        )
        yield TransferStatusTree(
            self,
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
            Horizontal(
                Button("Transfer", id="transfer_transfer_button"),
                Button("Options", id="transfer_options_button"),
                id="transfer_button_container",
            ),
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
            ("Not staged for transfer", "grey58"),
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

        self.query_one("#transfer_directorytree").update_transfer_tree()

    def on_select_changed(self, event: Select.Changed) -> None:
        """
        If "Top Level" transfer mode has been selected, updates
        DirectoryTree styling.
        """
        if self.query_one("#transfer_toplevel_radiobutton").value:
            self.project.set_top_level_folder(event.value)

            transfer_tree = self.query_one("#transfer_directorytree")
            transfer_tree.get_transfer_diffs()
            transfer_tree.update_transfer_tree()

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

    def transfer_data(self, transfer_bool: bool) -> None:
        """
        Executes data transfer using the parameters provided
        by the user.

        Parameters
        ----------
        transfer_bool: Passed by `ConfirmScreen`. True if user confirmed
            transfer by clicking "Yes".

        Returns
        -------
        None
        """

        if transfer_bool:
            upload_selected = not self.query_one("#transfer_switch").value

            if self.query_one("#transfer_all_radiobutton").value:
                try:
                    if upload_selected:
                        self.project.upload_entire_project()
                    else:
                        self.project.download_entire_project()
                except BaseException as e:
                    self.mainwindow.show_modal_error_dialog(str(e))
                    return

            elif self.query_one("#transfer_toplevel_radiobutton").value:
                try:
                    if upload_selected:
                        self.project.upload_all()
                    else:
                        self.project.download_all()
                except BaseException as e:
                    self.mainwindow.show_modal_error_dialog(str(e))
                    return

            elif self.query_one("#transfer_custom_radiobutton").value:
                try:
                    if upload_selected:
                        self.project.upload(
                            sub_names=self.query_one("#transfer_subject_input")
                            .value.replace(" ", "")
                            .split(","),
                            ses_names=self.query_one("#transfer_session_input")
                            .value.replace(" ", "")
                            .split(","),
                            datatype=self.query_one(
                                "DatatypeCheckboxes"
                            ).datatype_out,
                        )
                    else:
                        self.project.download(
                            sub_names=self.query_one("#transfer_subject_input")
                            .value.replace(" ", "")
                            .split(","),
                            ses_names=self.query_one("#transfer_session_input")
                            .value.replace(" ", "")
                            .split(","),
                            datatype=self.query_one(
                                "DatatypeCheckboxes"
                            ).datatype_out,
                        )
                except BaseException as e:
                    self.mainwindow.show_modal_error_dialog(str(e))
                    return

            transfer_tree = self.query_one("#transfer_directorytree")
            transfer_tree.get_transfer_diffs()
            transfer_tree.update_transfer_tree()

    @require_double_click
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        Upon double-clicking a directory within the directory-tree
        widget, append the file selected to the current contents of
        the \'Subject\' and/or \'Session\' input widgets, depending
        on the prefix of the directory selected.
        """
        if self.query_one("#transfer_custom_radiobutton").value:
            if event.path.stem.startswith("sub-"):
                if not self.query_one("#transfer_subject_input").value:
                    self.query_one(
                        "#transfer_subject_input"
                    ).value = f"{str(event.path.stem)}"
                else:
                    self.query_one(
                        "#transfer_subject_input"
                    ).value += f", {str(event.path.stem)}"
            if event.path.stem.startswith("ses-"):
                if not self.query_one("#transfer_session_input").value:
                    self.query_one(
                        "#transfer_session_input"
                    ).value = f"{str(event.path.stem)}"
                else:
                    self.query_one(
                        "#transfer_session_input"
                    ).value += f", {str(event.path.stem)}"


class TransferStatusTree(DirectoryTree):
    def __init__(self, parent_tab, project, id=None):
        super(TransferStatusTree, self).__init__(
            project.get_local_path(), id=id
        )

        self.parent_tab = parent_tab
        self.project = project
        self.get_transfer_diffs()

    def on_mount(self):
        self.transfer_paths = self.get_local_transfer_paths()

    def get_local_transfer_paths(self):
        """
        Compiles a list of all project files and paths staged for transfer
        using the parameters currently selected by the user.
        """

        all_paths = []
        walk_paths = walk(self.project.get_local_path().as_posix())
        # TODO: os.walk appends different file seps than those used by the datashuttle fxn.
        #  Still works, somehow, but ugly.
        for path in walk_paths:
            all_paths.append(path[0])
            if path[2]:
                all_paths.extend([f"{path[0]}/{file}" for file in path[2]])

        if self.parent_tab.query_one("#transfer_all_radiobutton").value:
            paths_out = [Path(path) for path in all_paths]

        elif self.parent_tab.query_one("#transfer_toplevel_radiobutton").value:
            toplevel_dir = (
                self.project.get_local_path()
                / self.project.cfg.top_level_folder
            )
            paths_out = [
                Path(path)
                for path in all_paths
                if all(part in Path(path).parts for part in toplevel_dir.parts)
            ]

        elif self.parent_tab.query_one("#transfer_custom_radiobutton").value:
            paths_out = [Path(path) for path in all_paths]

        else:
            paths_out = []

        return paths_out

    def get_transfer_diffs(self):
        """
        Updates the transfer diffs used to style the DirectoryTree.
        """
        self.transfer_diffs = get_local_and_central_file_differences(
            self.project.cfg
        )
        filtered_diffs = {
            key: self.transfer_diffs[key]
            for key in ["different", "local_only", "error"]
        }
        self.diff_paths = [
            path for category in filtered_diffs.values() for path in category
        ]

    def update_transfer_tree(self):
        """
        Updates tree styling to reflect the current TUI state
        and project transfer status.
        """

        self.transfer_paths = self.get_local_transfer_paths()
        self.reload()

    def render_label(
        self, node: TreeNode[DirEntry], base_style: Style, style: Style
    ) -> Text:
        """
        Extends the `DirectoryTree.render_label()` method to allow
        custom styling of file nodes according to their transfer status.
        """

        node_label = node._label.copy()
        node_label.stylize(style)

        node_path = node.data.path

        if node._allow_expand:
            prefix = (
                "📂 " if node.is_expanded else "📁 ",
                base_style + TOGGLE_STYLE,
            )
            node_label.stylize_before(
                self.get_component_rich_style(
                    "directory-tree--folder", partial=True
                )
            )
        else:
            prefix = (
                "📄 ",
                base_style,
            )
            node_label.stylize_before(
                self.get_component_rich_style(
                    "directory-tree--file", partial=True
                ),
            )
            node_label.highlight_regex(
                r"\..+$",
                self.get_component_rich_style(
                    "directory-tree--extension", partial=True
                ),
            )

        self.format_transfer_label(node_label, node_path)

        text = Text.assemble(prefix, node_label)
        return text

    def format_transfer_label(self, node_label, node_path):
        """
        Takes nodes being formatted using `render_label` and applies custom
        formatting according to the node's transfer status.
        """

        node_relative_path = node_path.as_posix().replace(
            f"{self.project.cfg.get_base_folder('local').as_posix()}/", ""
        )

        # Checks whether the current node's file path is staged for transfer
        if node_path in self.transfer_paths:
            # Sets sub- and ses-level folders to orange if files within have changed
            if (
                node_path.stem.startswith("sub-")
                or node_path.stem.startswith("ses-")
                or node_path.stem in get_datatypes()
            ):
                files_have_changed = any(
                    node_relative_path in file for file in self.diff_paths
                )
                if files_have_changed:
                    node_label.stylize_before("gold3")

            # Sets the top_level folder to orange if files within have changes
            elif (
                node_path.stem
                == self.project.get_top_level_folder()  # TODO: get_local_and_central_file_differences currently only checks for diffs in the current top-level folder
                and self.diff_paths
            ):
                node_label.stylize_before("gold3")

            # Assigns a color to project files according to transfer status
            else:
                if node_relative_path in self.transfer_diffs["same"]:
                    pass
                elif node_relative_path in self.transfer_diffs["different"]:
                    node_label.stylize_before("gold3")
                elif node_relative_path in self.transfer_diffs["local_only"]:
                    node_label.stylize_before("green3")
                elif node_label.plain in self.transfer_diffs["error"]:
                    node_label.stylize_before("bright_red")

        # Sets files that are not staged for transfer to grey
        else:
            node_label.stylize_before("grey58")
