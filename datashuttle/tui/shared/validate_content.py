from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Optional, Union, cast

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from datashuttle.tui.interface import Interface
    from datashuttle.tui.screens.project_manager import ProjectManagerScreen

from pathlib import Path

from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Checkbox,
    Label,
    RichLog,
    Select,
)

from datashuttle.datashuttle_functions import quick_validate_project
from datashuttle.tui.custom_widgets import ClickableInput
from datashuttle.tui.screens import modal_dialogs, validate_at_path
from datashuttle.tui.tooltips import get_tooltip


class ValidateContent(Container):
    """A container containing widgets for project validation.

    This is shared between the Validate Project from Path
    and validation tab on the project manager. It takes a similar
    approach to ConfigsContent.

    Todo:
    ----
    In contrast to ConfigsContent, these contents are always
    split. This should probably be factored into two classes
    with a shared base class.

    """

    def __init__(
        self,
        parent_class: Union[
            ProjectManagerScreen, validate_at_path.ValidateScreen
        ],
        interface: Optional[Interface],
        id: str,
    ) -> None:
        """Initialise the ValidateContent class.

        parent_class
            The parent screen (project manager or validate from path).

        interface
            Datashuttle Interface class.

        id
            Textual ID for the container.
        """
        super(ValidateContent, self).__init__(id=id)

        self.parent_class = parent_class
        self.interface = interface

    def compose(self) -> ComposeResult:
        """Set up the widgets for the container."""
        if platform.system() == "Windows":
            example_path = r"C:\path\to\project\project_name"
        else:
            example_path = "/mydrive/path/to/project/project_name"

        widgets = [
            Label("Path to project:", id="validate_path_label"),
            Horizontal(
                ClickableInput(
                    self.parent_class.mainwindow,
                    placeholder=f"e.g. {example_path}",
                    id="validate_path_input",
                ),
                Button("Select", id="validate_select_button"),
                id="validate_path_container",
            ),
            Horizontal(
                Select(
                    (
                        (name, name)
                        for name in ["rawdata", "derivatives", "both"]
                    ),
                    value="rawdata",
                    allow_blank=False,
                    id="validate_top_level_folder_select",
                ),
                Checkbox(
                    "Include Central",
                    value=False,
                    id="validate_include_central_checkbox",
                ),
                Checkbox(
                    "Strict Mode",
                    value=False,
                    id="validate_strict_mode_checkbox",
                ),
                id="validate_arguments_horizontal",
            ),
            RichLog(highlight=True, markup=True, id="validate_richlog"),
            Label("", id="validate_logs_label"),
            Button("Validate", id="validate_validate_button"),
        ]

        yield Container(*widgets, id="validate_top_container")

    def on_mount(self) -> None:
        """Handle the widgets immediately after they are mounted."""
        for id in [
            "validate_path_input",
            "validate_top_level_folder_select",
            "validate_include_central_checkbox",
            "validate_strict_mode_checkbox",
        ]:
            self.query_one(f"#{id}").tooltip = get_tooltip(id)

        if self.interface:
            for id in [
                "validate_path_input",
                "validate_path_container",
                "validate_select_button",
                "validate_path_label",
            ]:
                self.query_one(f"#{id}").remove()

            if self.interface.project.is_local_project():
                self.query_one("#validate_include_central_checkbox").remove()
        else:
            self.query_one("#validate_include_central_checkbox").remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle a button press event."""
        if event.button.id == "validate_select_button":
            self.parent_class.mainwindow.push_screen(
                modal_dialogs.SelectDirectoryTreeScreen(
                    self.parent_class.mainwindow
                ),
                lambda path_: self.set_select_path(path_),
            )

        elif event.button.id == "validate_validate_button":
            select_value = self.query_one(
                "#validate_top_level_folder_select"
            ).value
            top_level_folder = None if select_value == "both" else select_value
            strict_mode = self.query_one(
                "#validate_strict_mode_checkbox"
            ).value

            #            assert False, f"strict mode: {strict_mode}"

            if self.interface:
                if self.interface.project.is_local_project():
                    include_central = False
                else:
                    include_central = self.query_one(
                        "#validate_include_central_checkbox"
                    ).value

                success, output = self.interface.validate_project(
                    top_level_folder=top_level_folder,
                    include_central=include_central,
                    strict_mode=strict_mode,
                )
                if not success:
                    self.parent_class.mainwindow.show_modal_error_dialog(
                        cast("str", output)
                    )
                else:
                    self.write_results_to_richlog(output)
                    self.query_one(
                        "#validate_logs_label"
                    ).value = f"Logs output to: {self.interface.project.get_logging_path()}"
            else:
                path_ = self.query_one("#validate_path_input").value

                if path_ == "":
                    self.parent_class.mainwindow.show_modal_error_dialog(
                        "Input a path to perform validation."
                    )
                    return

                if not Path(path_).is_dir():
                    self.parent_class.mainwindow.show_modal_error_dialog(
                        f"No folder found at path: {path_}"
                    )
                    return

                output = quick_validate_project(
                    path_,
                    top_level_folder=top_level_folder,
                    strict_mode=strict_mode,
                )
                self.write_results_to_richlog(output)

    def set_select_path(self, path_):
        """Fill the Input with the path_ if it is not None."""
        if path_:
            self.query_one("#validate_path_input").value = path_.as_posix()

    def write_results_to_richlog(self, results):
        """Display the validation results on the Rich Log widget."""
        text_log = self.query_one("#validate_richlog")
        text_log.clear()
        if any(results):
            text_log.write("\n".join(results))
        else:
            text_log.write("No issues found.")
