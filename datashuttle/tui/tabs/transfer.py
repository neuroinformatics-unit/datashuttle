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
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TOGGLE_STYLE, TreeNode

from datashuttle.configs import canonical_folders
from datashuttle.configs.canonical_configs import get_datatypes
from datashuttle.configs.canonical_folders import get_top_level_folders
from datashuttle.tui.custom_widgets import DatatypeCheckboxes, FilteredTree
from datashuttle.tui.screens.modal_dialogs import ConfirmScreen
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
                " Existing data with \nthe same file details on central will not be \noverwritten."
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
                value=canonical_folders.get_top_level_folders()[0],
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
                validate_on=["changed", "submitted"],
            ),
            Label("Session(s)"),
            Input(
                id="transfer_session_input",
                placeholder="e.g. ses-001",
                validate_on=["changed", "submitted"],
            ),
            Label("Datatype(s)"),
            DatatypeCheckboxes(self.project),
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
            ("Central Only\n", "dodger_blue3"),
            ("Error\n", "bright_red"),
            ("Not staged for transfer", "grey58"),
        )

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        Update the displayed transfer parameter widgets when the
        `transfer_radioset` radiobuttons are changed.
        """
        label = str(event.pressed.label)
        assert label in ["All", "Top Level", "Custom"], "Unexpected label."
        self.switch_transfer_widgets_display()

        self.transfer_paths = self.get_transfer_paths()
        self.query_one("#transfer_directorytree").reload()

    def get_transfer_paths(self):
        all_paths = []
        walk_paths = walk(self.project.get_local_path().as_posix())
        # TODO: os.walk appends different file seps than those used by the datashuttle fxn.
        #  Still works, somehow, but ugly.
        for path in walk_paths:
            all_paths.append(path[0])
            if path[2]:
                all_paths.extend([f"{path[0]}/{file}" for file in path[2]])

        if self.query_one("#transfer_all_radiobutton").value:
            paths_out = [Path(path) for path in all_paths]

        elif self.query_one("#transfer_toplevel_radiobutton").value:
            toplevel_dir = (
                self.project.get_local_path()
                / self.project.cfg.top_level_folder
            )
            paths_out = [
                Path(path)
                for path in all_paths
                if all(part in Path(path).parts for part in toplevel_dir.parts)
            ]

        elif self.query_one("#transfer_custom_radiobutton").value:
            paths_out = []  # TODO: Come back to this...

        else:
            paths_out = []

        return paths_out

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

    def on_select_changed(self, event: Select.Changed) -> None:
        """
        If "Top Level" transfer mode has been selected, updates
        DirectoryTree styling.
        """
        if self.query_one("#transfer_toplevel_radiobutton").value:
            self.project.set_top_level_folder(event.value)

            self.transfer_paths = self.get_transfer_paths()
            self.query_one("#transfer_directorytree").reload()

    def on_button_pressed(self, event: Button.Pressed) -> None:
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
                f" the selected data {preposition} \nthis project's configured",
                " central filesystem.\n\nAre you sure you wish to proceed?\n",
            )

            self.mainwindow.push_screen(
                ConfirmScreen(message), self.transfer_data
            )

    def transfer_data(self, transfer_bool: bool) -> None:
        if transfer_bool:
            upload_selected = not self.query_one("#transfer_switch").value

            if self.query_one("#transfer_all_radiobutton").value:
                if upload_selected:
                    self.project.upload_entire_project()
                else:
                    self.project.download_entire_project()

            elif self.query_one("#transfer_toplevel_radiobutton").value:
                if upload_selected:
                    self.project.upload_all()
                else:
                    self.project.download_all()

            elif self.query_one("#transfer_custom_radiobutton").value:
                if upload_selected:
                    self.project.upload(
                        sub_names=self.query_one("#transfer_subject_input")
                        .replace(" ", "")
                        .split(","),
                        ses_names=self.query_one("#transfer_session_input")
                        .replace(" ", "")
                        .split(","),
                        datatype=self.query_one(
                            "DatatypeCheckboxes"
                        ).datatype_out,
                    )
                else:
                    self.project.download(
                        sub_names=self.query_one("#transfer_subject_input")
                        .replace(" ", "")
                        .split(","),
                        ses_names=self.query_one("#transfer_session_input")
                        .replace(" ", "")
                        .split(","),
                        datatype=self.query_one(
                            "DatatypeCheckboxes"
                        ).datatype_out,
                    )

            self.update_transfer_tree()

    def update_transfer_tree(self):
        self.transfer_paths = self.get_transfer_paths()

        transfer_tree = self.query_one("#transfer_directorytree")
        transfer_tree.transfer_diffs = get_local_and_central_file_differences(
            self.project.cfg
        )
        transfer_tree.all_diffs = [
            path
            for category in transfer_tree.transfer_diffs.values()
            for path in category
        ]
        transfer_tree.reload()


class TransferStatusTree(FilteredTree):
    def __init__(self, parent_tab, project, id=None):
        super(TransferStatusTree, self).__init__(
            project.get_local_path(), id=id
        )

        self.tab = parent_tab
        self.project = project
        self.transfer_diffs = get_local_and_central_file_differences(
            project.cfg
        )
        self.all_diffs = [
            path
            for category in self.transfer_diffs.values()
            for path in category
        ]

    def on_mount(self):
        self.tab.transfer_paths = self.tab.get_transfer_paths()

    def render_label(
        self, node: TreeNode[DirEntry], base_style: Style, style: Style
    ) -> Text:
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

        self.format_transfer_label(node, node_label, node_path)

        if (
            node_label.plain.startswith(".")
            or node_path not in self.tab.transfer_paths
        ):
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--hidden")
                # "grey58"
            )

        text = Text.assemble(prefix, node_label)
        return text

    def format_transfer_label(self, node, node_label, node_path):
        node_relative_path = node_path.as_posix().replace(
            self.project.cfg.get_base_folder("local").as_posix() + "/", ""
        )

        if (
            node_path.stem.startswith("sub-")
            or node_path.stem.startswith("ses-")
            or node_path.stem in get_datatypes()
        ) and not node.is_expanded:
            if any(node_relative_path in file for file in self.all_diffs):
                node_label.stylize_before("gold3")

        elif (
            node_path.stem in get_top_level_folders()
            and not node.is_expanded
            and self.all_diffs
        ):
            node_label.stylize_before("gold3")

        else:
            if node_relative_path in self.transfer_diffs["same"]:
                pass
            elif node_relative_path in self.transfer_diffs["different"]:
                node_label.stylize_before("gold3")
            elif node_relative_path in self.transfer_diffs["local_only"]:
                node_label.stylize_before("green3")
            elif node_relative_path in self.transfer_diffs["central_only"]:
                node_label.stylize_before("dodger_blue3")
                # TODO: -> These nodes need to be added manually.
                #  Make new function to add relevant nodes and style
                #  them.
            elif node_label.plain in self.transfer_diffs["error"]:  #
                node_label.stylize_before("bright_red")
