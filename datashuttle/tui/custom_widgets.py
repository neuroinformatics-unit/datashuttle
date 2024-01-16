from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, cast

if TYPE_CHECKING:
    from textual import events
from dataclasses import dataclass

from rich.style import Style
from rich.text import Text
from textual._segment_tools import line_pad
from textual.message import Message
from textual.strip import Strip
from textual.widgets import Checkbox, DirectoryTree, Input, Static


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

    def _on_click(self, click: events.Click) -> None:
        self.post_message(self.Clicked(self, click.button))

    def as_names_list(self):
        return self.value.replace(" ", "").split(",")


class CustomDirectoryTree(DirectoryTree):
    """
    Add a custom Directory tree that overrides `_render_line` to stop hover CSS
    applied to guide (as it was distracting) and cursor CSS added on file / folder
    click (as it removed existing style that indicates the transfer status).

    TODO
    ----
    This is really a temporary solution and should be handled better,
    see textual issue #4028
    """

    def _render_line(
        self, y: int, x1: int, x2: int, base_style: Style
    ) -> Strip:
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
