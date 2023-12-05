from os import walk
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    DirectoryTree,
    Input,
    Label,
    RadioButton,
    RadioSet,
    TabPane,
)
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TOGGLE_STYLE, TreeNode

from datashuttle.tui.custom_widgets import DatatypeCheckboxes
from datashuttle.tui.utils.tui_decorators import require_double_click
from datashuttle.tui.utils.tui_validators import NeuroBlueprintValidator
from datashuttle.utils.rclone import get_local_and_central_file_differences


class TransferTab(TabPane):
    def __init__(self, mainwindow, project):
        super(TransferTab, self).__init__(
            "Transfer", id="tabscreen_transfer_tab"
        )
        self.mainwindow = mainwindow
        self.project = project
        self.toplevel = self.project.cfg.get_base_folder("local")

        self.prev_click_time = 0.0

    def compose(self):
        self.transfer_all_widgets = [  # TODO: Check if rawdata and derivatives can have different names?
            Label(
                "All data from: \n\n - Rawdata \n - Derivatives \n\nWill be transferred."
                " Existing data with \nthe same file details on central will not be \noverwritten.",
                id="transfer_all_label",
            )
        ]

        self.transfer_toplevel_widgets = [
            Label(
                "Double-click file tree to choose top-level \nfolder to transfer",
                id="transfer_toplevel_label_top",
            ),
            Input(
                value=self.toplevel.stem,
                disabled=True,
                id="transfer_toplevel_input",
            ),
            Label(
                "Existing data with the same file details on \ncentral will not be overwritten by default."
            ),
        ]

        self.transfer_custom_widgets = [
            Label("Subject(s)", id="tabscreen_subject_label"),
            Input(
                id="tabscreen_subject_input",
                placeholder="e.g. sub-001",
                validate_on=["changed", "submitted"],
                validators=[NeuroBlueprintValidator("sub", self)],
            ),
            Label("Session(s)", id="tabscreen_session_label"),
            Input(
                id="tabscreen_session_input",
                placeholder="e.g. ses-001",
                validate_on=["changed", "submitted"],
                validators=[NeuroBlueprintValidator("ses", self)],
            ),
            Label("Datatype(s)", id="tabscreen_datatype_label"),
            DatatypeCheckboxes(self.project),
        ]

        yield TransferStatusTree(
            self,
            self.project,
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
            Button("Transfer"),
            Button("Options"),
        )

    def on_mount(self):
        self.query_one(
            "#transfer_params_container"
        ).border_title = "Parameters"
        self.switch_transfer_widgets_display()

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
        walk_paths = walk(self.project.cfg.get_base_folder("local").as_posix())
        # TODO: os.walk appends different file seps than those used by the datashuttle fxn.
        #  Still works, somehow, but ugly.
        for path in walk_paths:
            all_paths.append(path[0])
            if path[2]:
                all_paths.extend([f"{path[0]}/{file}" for file in path[2]])

        if self.query_one("#transfer_all_radiobutton").value:
            paths_out = [Path(path) for path in all_paths]

        elif self.query_one("#transfer_toplevel_radiobutton").value:
            # toplevel_dir = self.query_one("#transfer_toplevel_input").value
            toplevel_dir = self.toplevel
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

    @require_double_click
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        If "Top Level" transfer mode has been selected, replaces
        contents of the "Top Level" input widget and updates
        DirectoryTree styling.

        Double-click time is set to the Windows default duration (500 ms).
        """
        if self.query_one("#transfer_toplevel_radiobutton").value:
            self.toplevel = event.path
            self.query_one("#transfer_toplevel_input").value = event.path.stem

            self.transfer_paths = self.get_transfer_paths()
            self.query_one("#transfer_directorytree").reload()


class TransferStatusTree(DirectoryTree):
    def __init__(self, parent_tab, project, id=None):
        super(TransferStatusTree, self).__init__(
            project.cfg.data["local_path"], id=id
        )

        self.tab = parent_tab
        self.project = project
        self.transfer_diffs = get_local_and_central_file_differences(
            project.cfg
        )

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

        self.format_transfer_label(node_label, node_path)

        if (
            node_label.plain.startswith(".")
            or node_path not in self.tab.transfer_paths
        ):
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--hidden")
            )

        text = Text.assemble(prefix, node_label)
        return text

    def format_transfer_label(self, node_label, node_path):
        node_relative_path = node_path.as_posix().replace(
            self.project.cfg.get_base_folder("local").as_posix() + "/", ""
        )

        if node_relative_path in self.transfer_diffs["same"]:
            pass

        elif node_relative_path in self.transfer_diffs["different"]:
            node_label.stylize_before("gold3")

        elif node_relative_path in self.transfer_diffs["local_only"]:
            node_label.stylize_before("green3")

        elif node_relative_path in self.transfer_diffs["central_only"]:
            node_label.stylize_before("dodger_blue3")
            # TODO: -> Won't be able to handle this at first.
            #  Make new function to add relevant nodes and style
            #  them.

        elif node_label.plain in self.transfer_diffs["error"]:  #
            node_label.stylize_before("bright_red")
