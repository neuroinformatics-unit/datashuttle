from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Optional, cast

if TYPE_CHECKING:
    from pathlib import Path

    from textual import events

from dataclasses import dataclass

import pyperclip
from rich.style import Style
from rich.text import Text
from textual._segment_tools import line_pad
from textual.message import Message
from textual.strip import Strip
from textual.widgets import Checkbox, DirectoryTree, Input, Static, TabPane

# --------------------------------------------------------------------------------------
# DatatypeCheckboxes
# --------------------------------------------------------------------------------------


class DatatypeCheckboxes(Static):
    """
    Dynamically-populated checkbox widget for convenient datatype
    selection during folder creation.

    Parameters
    ----------

    settings_key : 'create' if datatype checkboxes for the create tab,
                   'transfer' for the transfer tab. Transfer tab includes
                   additional datatype options (e.g. "all").

    Attributes
    ----------

    datatype_config : a Dictionary containing datatype as key (e.g. "ephys", "behav")
                      and values are `bool` indicating whether the checkbox is on / off.
                      If 'transfer', then transfer datatype arguments (e.g. "all")
                      are also included. This structure mirrors
                      the `persistent_settings` dictionaries.
    """

    def __init__(self, project, create_or_transfer="create"):
        super(DatatypeCheckboxes, self).__init__()

        self.project = project

        if create_or_transfer == "create":
            self.settings_key = "create_checkboxes_on"
        else:
            self.settings_key = "transfer_checkboxes_on"

        self.datatype_config = self.project._load_persistent_settings()["tui"][
            self.settings_key
        ]

    def compose(self):
        for datatype in self.datatype_config.keys():
            yield Checkbox(
                datatype.title(),
                id=f"tabscreen_{datatype}_checkbox",
                value=self.datatype_config[datatype],
            )

    def on_checkbox_changed(self):
        """
        When a checkbox is changed, update the `self.datatype_config`
        to contain new boolean values for each datatype. Also update
        the stored `persistent_settings`.
        """
        for datatype in self.datatype_config.keys():
            self.datatype_config[datatype] = self.query_one(
                f"#tabscreen_{datatype}_checkbox"
            ).value

        # This is slightly wasteful as update entire dict instead
        # of changed entry, but is negligible.
        persistent_settings = self.project._load_persistent_settings()
        persistent_settings["tui"][self.settings_key] = self.datatype_config
        self.project._save_persistent_settings(persistent_settings)

    def selected_datatypes(self) -> List[str]:
        """
        Get the names of the datatype options for which the
        checkboxes are switched on.
        """
        selected_datatypes = [
            datatype
            for datatype, is_on in self.datatype_config.items()
            if is_on
        ]
        return selected_datatypes


# --------------------------------------------------------------------------------------
# ClickableInput
# --------------------------------------------------------------------------------------


class ClickableInput(Input):
    """
    An input widget which emits a `ClickableInput.Clicked`
    signal when clicked, containing the input name
    `input` and mouse button index `button`.
    """

    @dataclass
    class Clicked(Message):
        input: ClickableInput
        button: int

    def _on_click(self, event: events.Click) -> None:
        self.post_message(self.Clicked(self, event.button))

    def as_names_list(self):
        return self.value.replace(" ", "").split(",")


# --------------------------------------------------------------------------------------
# CustomDirectoryTree
# --------------------------------------------------------------------------------------


class CustomDirectoryTree(DirectoryTree):
    @dataclass
    class DirectoryTreeKeyPress(Message):
        key: str
        node_path: Optional[Path]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """
        Filter out the top level .datashuttle folder than contains logs from
        the directorytree display.

        `paths` below are only the folders within the root folder. So this will
        filter out .datashuttle only at the root and not all instances of
        .datashuttle lower down which I suppose we may want visible.
        """
        return [
            path for path in paths if not path.name.startswith(".datashuttle")
        ]

    def on_key(self, event: events.Key):
        """
        Handle key presses on the CustomDirectoryTree. Depending on the keys pressed,
        copy the path under the cursor, refresh the directorytree or
        emit a DirectoryTreeKeyPress event.
        """
        if event.key == "ctrl+q":
            path_ = self.get_node_at_line(self.hover_line).data.path
            pyperclip.copy(path_.as_posix())

        elif event.key == "ctrl+r":
            self.reload_directorytree()

        elif event.key in ["ctrl+a", "ctrl+f"]:
            path_ = self.get_node_at_line(self.hover_line).data.path
            self.post_message(
                self.DirectoryTreeKeyPress(event.key, node_path=path_)
            )

    def reload_directorytree(self):
        """
        A function to reload the DirectoryTree, typically called at the tab-level.
        This can optionally perform some logic before calling `self.reload()`.
        """
        raise NotImplementedError(
            "Must implement this method in child classes."
        )

    # Overridden Methods
    # ----------------------------------------------------------------------------------

    def _render_line(
        self, y: int, x1: int, x2: int, base_style: Style
    ) -> Strip:
        """
        This function is overridden from textual's `Tree` class to stop
        CSS styling on hovering and clicking which was distracting /
        changed the default color used for transfer status, respectively.

        Note better approaches should be possible, see textual issue #4028.
        """
        tree_lines = self._tree_lines
        width = self.size.width

        if y >= len(tree_lines):
            return Strip.blank(width, base_style)

        line = tree_lines[y]

        is_hover = self.hover_line >= 0 and any(
            node._hover for node in line.path
        )

        cache_key = (
            y,
            is_hover,
            width,
            self._updates,
            self._pseudo_class_state,
            tuple(node._updates for node in line.path),
        )
        if cache_key in self._line_cache:
            strip = self._line_cache[cache_key]
        else:
            base_guide_style = self.get_component_rich_style(
                "tree--guides", partial=True
            )
            guide_hover_style = base_guide_style
            #            guide_hover_style = base_guide_style +
            #            self.get_component_rich_style(
            #               "tree--guides-hover", partial=True
            #          )
            guide_selected_style = (
                base_guide_style
                + self.get_component_rich_style(
                    "tree--guides-selected", partial=True
                )
            )

            hover = line.path[0]._hover
            selected = line.path[0]._selected and self.has_focus

            def get_guides(style: Style) -> tuple[str, str, str, str]:
                """Get the guide strings for a given style.

                Args:
                    style: A Style object.

                Returns:
                    Strings for space, vertical, terminator and cross.
                """
                lines: tuple[
                    Iterable[str], Iterable[str], Iterable[str], Iterable[str]
                ]
                if self.show_guides:
                    lines = self.LINES["default"]
                    if style.bold:
                        lines = self.LINES["bold"]
                    elif style.underline2:
                        lines = self.LINES["double"]
                else:
                    lines = ("  ", "  ", "  ", "  ")

                guide_depth = max(0, self.guide_depth - 2)
                guide_lines = tuple(
                    f"{characters[0]}{characters[1] * guide_depth} "  # type: ignore
                    for characters in lines
                )
                return cast("tuple[str, str, str, str]", guide_lines)

            if is_hover:
                line_style = self.get_component_rich_style(
                    "tree--highlight-line"
                )
            else:
                line_style = base_style

            guides = Text(style=line_style)
            guides_append = guides.append

            guide_style = base_guide_style
            for node in line.path[1:]:
                if hover:
                    guide_style = guide_hover_style
                if selected:
                    guide_style = guide_selected_style

                space, vertical, _, _ = get_guides(guide_style)
                guide = space if node.is_last else vertical
                if node != line.path[-1]:
                    guides_append(guide, style=guide_style)
                hover = hover or node._hover
                selected = (selected or node._selected) and self.has_focus

            if len(line.path) > 1:
                _, _, terminator, cross = get_guides(guide_style)
                if line.last:
                    guides.append(terminator, style=guide_style)
                else:
                    guides.append(cross, style=guide_style)

            label_style = self.get_component_rich_style(
                "tree--label", partial=True
            )
            if self.hover_line == y:
                label_style += self.get_component_rich_style(
                    "tree--highlight", partial=True
                )
            #            if self.cursor_line == y:
            #               label_style += self.get_component_rich_style(
            #                  "tree--cursor", partial=False
            #             )

            label = self.render_label(
                line.path[-1], line_style, label_style
            ).copy()
            label.stylize(Style(meta={"node": line.node._id, "line": y}))
            guides.append(label)

            segments = list(guides.render(self.app.console))
            pad_width = max(self.virtual_size.width, width)
            segments = line_pad(
                segments, 0, pad_width - guides.cell_len, line_style
            )
            strip = self._line_cache[cache_key] = Strip(segments)

        strip = strip.crop(x1, x2)
        return strip


# --------------------------------------------------------------------------------------
# TreeAndInputTab
# --------------------------------------------------------------------------------------


class TreeAndInputTab(TabPane):
    """
    A parent class that defined common methods for screens with
    a directory tree and sub / session inputs, .e. the Create tab
    and the Transfer tab.
    """

    def handle_directorytree_key_pressed(
        self, sub_input_key, ses_input_key, event
    ):
        """
        When a CustomDirectoryTree key is pressed, we typically
        want to perform an action that involves an Input. These are
        coordinated here. Note that the 'copy' and 'refresh'
        features of the tree is handled at the level of the
        CustomDirectoryTree.

        Event Keys
        ----------

        "ctrl+a" : When CTRL and A are held at the same time, the sub / ses
                   node under the mouse is appended to the relevant Input

        "ctrl+f" : When CTRL and F are held at the same time, the sub / ses node
                  under the mouse is filled into the relevant Input (i.e. previous
                  value deleted).

        Parameters
        ----------

        sub_input_key : str
            The textual widget id for the subject input (prefixed with #)

        ses_input_key : str
            The textual widget id for the session input (prefixed with #)

        event : DirectoryTreeKeyPress
            A DirectoryTreeKeyPress event triggered from the
            CustomDirectoryTree.
        """
        if event.key == "ctrl+a":
            self.append_sub_or_ses_name_to_input(
                sub_input_key,
                ses_input_key,
                name=event.node_path.stem,
            )
        elif event.key == "ctrl+f":
            self.insert_sub_or_ses_name_to_input(
                sub_input_key,
                ses_input_key,
                name=event.node_path.stem,
            )

    def insert_sub_or_ses_name_to_input(
        self, sub_input_key, ses_input_key, name
    ):
        """
        see `handle_directorytree_keQy_pressed` for `sub_input_key` and
        `ses_input_key`.

        name : str
            The sub or ses name to append to the input.
        """
        if name.startswith("sub-"):
            self.query_one(sub_input_key).value = name
        elif name.startswith("ses-"):
            self.query_one(ses_input_key).value = name

    def append_sub_or_ses_name_to_input(
        self, sub_input_key, ses_input_key, name
    ):
        """
        see `insert_sub_or_ses_name_to_input`.
        """
        if name.startswith("sub-"):
            if not self.query_one(sub_input_key).value:
                self.query_one(sub_input_key).value = name
            else:
                self.query_one(sub_input_key).value += f", {name}"

        if name.startswith("ses-"):
            if not self.query_one(ses_input_key).value:
                self.query_one(ses_input_key).value = name
            else:
                self.query_one(ses_input_key).value += f", {name}"

    def get_sub_ses_names_and_datatype(self, sub_input_key, ses_input_key):
        """
        see `handle_directorytree_key_pressed` for parameters.
        """
        sub_names = self.query_one(sub_input_key).as_names_list()
        ses_names = self.query_one(ses_input_key).as_names_list()
        datatype = self.query_one("DatatypeCheckboxes").selected_datatypes()

        return sub_names, ses_names, datatype
