from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:

    from rich.style import Style
    from textual.widgets._directory_tree import DirEntry

    from datashuttle.tui.app import App
    from datashuttle.tui.interface import Interface

import os
from pathlib import Path

from rich.text import Text
from textual.widgets._tree import TOGGLE_STYLE, TreeNode

from datashuttle.configs import canonical_folders
from datashuttle.tui.custom_widgets import (
    CustomDirectoryTree,
)
from datashuttle.utils.rclone import get_local_and_central_file_differences


class TransferStatusTree(CustomDirectoryTree):
    """
    A directorytree in which the nodes are styled depending on their
    transfer status. e.g. indicates whether files are changed between
    local or central, or appear in local only.

    Attributes
    ----------

    Keep the local path as a string, linked to project.cfg["local_path"],
    so that no conversion to string is necessary in `format_transfer_label`
    which is called many times.
    """

    def __init__(
        self, mainwindow: App, interface: Interface, id: Optional[str] = None
    ):

        self.interface = interface
        self.local_path_str = self.interface.get_configs()[
            "local_path"
        ].as_posix()
        self.transfer_diffs: Dict = {}

        super(TransferStatusTree, self).__init__(
            path=self.local_path_str, mainwindow=mainwindow, id=id
        )

    def on_mount(self) -> None:
        self.update_transfer_tree(init=True)

    def update_transfer_tree(self, init: bool = False) -> None:
        """
        Updates tree styling to reflect the current TUI state
        and project transfer status.
        """
        self.local_path_str = self.interface.get_configs()[
            "local_path"
        ].as_posix()

        self.update_local_transfer_paths()

        if self.mainwindow.load_global_settings()["show_transfer_tree_status"]:
            self.update_transfer_diffs()

        if not init:
            self.reload()

    def update_local_transfer_paths(self) -> None:
        """
        Compiles a list of all project files and paths.
        """
        paths_list = []

        for top_level_folder in canonical_folders.get_top_level_folders():
            walk_paths = os.walk(f"{self.local_path_str}/{top_level_folder}")
            for path in walk_paths:
                paths_list.append(Path(path[0]))
                if path[2]:
                    paths_list.extend(
                        [Path(f"{path[0]}/{file}") for file in path[2]]
                    )
        self.transfer_paths = paths_list

    def update_transfer_diffs(self) -> None:
        """
        Updates the transfer diffs used to style the DirectoryTree.
        """
        self.transfer_diffs = get_local_and_central_file_differences(
            self.interface.get_configs(),
            top_level_folders_to_check=["rawdata", "derivatives"],
        )

    # Overridden Methods
    # ----------------------------------------------------------------------------------

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

        if self.transfer_diffs:
            self.format_transfer_label(node_label, node_path)

        text = Text.assemble(prefix, node_label)
        return text

    def format_transfer_label(self, node_label, node_path) -> None:
        """
        Takes nodes being formatted using `render_label` and applies custom
        formatting according to the node's transfer status.
        """
        node_relative_path = node_path.as_posix().replace(
            f"{self.local_path_str}/", ""
        )

        # Checks whether the current node's file path is staged for transfer
        if node_path in self.transfer_paths:
            # Sets sub- and ses-level folders to orange if files within have changed
            # fmt: off
            if node_relative_path in self.transfer_diffs["same"]:
                pass
            elif node_relative_path in self.transfer_diffs["different"] or any([node_relative_path in file for file in self.transfer_diffs["different"]]):
                node_label.stylize_before("gold3")
            elif node_relative_path in self.transfer_diffs["local_only"] or any([node_relative_path in file for file in self.transfer_diffs["local_only"]]):
                node_label.stylize_before("green3")
            elif node_label.plain in self.transfer_diffs["error"] or any([node_relative_path in file for file in self.transfer_diffs["error"]]):
                node_label.stylize_before("bright_red")
            # fmt: on
