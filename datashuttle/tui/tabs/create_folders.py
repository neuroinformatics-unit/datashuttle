from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from time import monotonic
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from textual.events import Click

from textual import on
from textual.containers import Horizontal
from textual.message import Message
from textual.validation import ValidationResult, Validator
from textual.widgets import (
    Button,
    DirectoryTree,
    Input,
    Label,
    TabPane,
)

from datashuttle.tui import custom_widgets
from datashuttle.tui.screens.create_folders_settings import (
    TemplateSettingsScreen,
)
from datashuttle.utils import formatting, validation


class ClickableInput(Input):
    @dataclass
    class Clicked(Message):
        input: ClickableInput
        button: int

    def _on_click(self, click: Click) -> None:
        self.post_message(self.Clicked(self, click.button))


def require_double_click(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        create_folders_tab_class = args[0]

        click_time = monotonic()

        if click_time - create_folders_tab_class.prev_click_time < 0.5:
            create_folders_tab_class.prev_click_time = click_time
            return func(*args, **kwargs)
        create_folders_tab_class.prev_click_time = click_time

    return wrapper


class CreateFoldersTab(TabPane):
    """
    From this tab, the user can easily create new project files
    formatted according to the NeuroBlueprint specification.
    """

    def __init__(self, mainwindow, project):
        super(CreateFoldersTab, self).__init__(
            "Create", id="tabscreen_create_tab"
        )
        self.mainwindow = mainwindow
        self.project = project

        self.prev_click_time = 0.0

        self.templates = project.get_name_templates()

    def compose(self):
        yield DirectoryTree(
            self.project.cfg.data["local_path"],
            id="tabscreen_directorytree",
        )
        yield Label("Subject(s)", id="tabscreen_subject_label")
        yield ClickableInput(
            id="tabscreen_subject_input",
            placeholder="e.g. sub-001",
            validate_on=["changed", "submitted"],
            validators=[QuickNeuroBlueprintValidator("sub", self)],
        )
        yield Label("Session(s)", id="tabscreen_session_label")
        yield ClickableInput(
            id="tabscreen_session_input",
            placeholder="e.g. ses-001",
            validate_on=["changed", "submitted"],
            validators=[QuickNeuroBlueprintValidator("ses", self)],
        )
        yield Label("Datatype(s)", id="tabscreen_datatype_label")
        yield custom_widgets.DatatypeCheckboxes(self.project)
        yield Button("Make Folders", id="tabscreen_make_folder_button")
        yield Horizontal(
            Horizontal(),
            Button(
                "Template Settings", id="tabscreen_template_settings_button"
            ),
        )

    @on(ClickableInput.Clicked)
    @require_double_click
    def log_click(self, event: ClickableInput.Clicked) -> None:
        input_id = event.input.id
        assert input_id in [
            "tabscreen_session_input",
            "tabscreen_subject_input",
        ], "unknown input name"

        prefix = "sub" if "subject" in input_id else "ses"

        # TODO: it is highly unliekly these idx are robust
        # across machines
        if event.button == 1:
            self.fill_input_with_template(prefix, input_id)
        elif event.button == 3:
            self.fill_input_with_next_sub_or_ses_template(prefix, input_id)

    def fill_input_with_template(self, prefix, input_id):
        """"""
        if self.templates["on"]:
            fill_value = self.templates[prefix]
        else:
            fill_value = f"{prefix}-"

        input = self.query_one(f"#{input_id}")
        input.value = fill_value

    def fill_input_with_next_sub_or_ses_template(self, prefix, input_id):
        # may be a more robust way...
        if prefix == "sub":
            next_val = self.project.get_next_sub_number(
                return_with_prefix=True, local_only=True
            )
        else:
            # TODO: this will crash sometimes...
            sub = self.query_one("#tabscreen_subject_input").value
            next_val = self.project.get_next_ses_number(
                sub, return_with_prefix=True, local_only=True
            )
        if self.templates["on"]:
            split_name = self.templates[prefix].split("_")
            fill_value = "_".join([next_val, *split_name[1:]])
        else:
            fill_value = next_val

        input = self.query_one(f"#{input_id}")
        input.value = fill_value

    @require_double_click
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        Upon double-clicking a directory within the directory-tree
        widget, replace contents of the \'Subject\' and/or \'Session\'
        input widgets, depending on the prefix of the directory selected.
        Double-click time is set to the Windows default duration (500 ms).
        """
        #   click_time = monotonic()
        #  if click_time - self.prev_click_time < 0.5:
        if event.path.stem.startswith("sub-"):
            self.query_one("#tabscreen_subject_input").value = str(
                event.path.stem
            )
        if event.path.stem.startswith("ses-"):
            self.query_one("#tabscreen_session_input").value = str(
                event.path.stem
            )

    # self.prev_click_time = click_time

    def on_button_pressed(self, event: Button.Pressed):
        """
        Enables the Make Folders button to read out current input values
        and use these to call project.make_folders().
        """

        if event.button.id == "tabscreen_make_folder_button":
            sub_dir = self.query_one("#tabscreen_subject_input").value
            ses_dir = self.query_one("#tabscreen_session_input").value

            if ses_dir == "":  # TODO: centralise this to func
                ses_dir = None

            try:
                self.project.make_folders(
                    sub_names=sub_dir,
                    ses_names=ses_dir,
                    datatype=self.query_one("DatatypeCheckboxes").datatype_out,
                )
                self.query_one("#tabscreen_directorytree").reload()
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return

        elif event.button.id == "tabscreen_template_settings_button":
            self.mainwindow.push_screen(
                TemplateSettingsScreen(self.mainwindow, self.project),
                self.update_templates,
            )

    def update_templates(self, templates):
        self.project.set_name_templates(templates)
        self.templates = templates
        self.revalidate_inputs(["sub", "ses"])

    def run_local_validation(self, prefix):
        """ """
        try:
            sub_dir = self.query_one("#tabscreen_subject_input").value

            format_sub = formatting.check_and_format_names(
                sub_dir, "sub", name_templates=self.templates
            )

            if prefix == "sub":
                format_ses = None
            else:
                ses_dir = self.query_one("#tabscreen_session_input").value

                format_ses = formatting.check_and_format_names(
                    ses_dir, "ses", name_templates=self.templates
                )

            validation.validate_names_against_project(
                self.project.cfg,
                format_sub,
                format_ses,
                local_only=True,
                error_or_warn="error",
                log=False,
                name_templates=self.templates,
            )

        except Exception as e:
            return False, str(e)

        names = format_sub if prefix == "sub" else format_ses

        return True, f"Formatted names: {names}"

    def update_input_tooltip(self, message: Optional[str], prefix):
        """ """
        id = (
            "#tabscreen_subject_input"
            if prefix == "sub"
            else "#tabscreen_session_input"
        )
        input = self.query_one(id)
        input.tooltip = message

    def revalidate_inputs(self, all_prefixes: List[str]):
        """"""
        input_names = {
            "sub": "#tabscreen_subject_input",
            "ses": "#tabscreen_session_input",
        }
        for prefix in all_prefixes:
            key = input_names[prefix]

            value = self.query_one(key).value
            self.query_one(key).validate(value=value)


class QuickNeuroBlueprintValidator(Validator):
    """"""

    def __init__(self, prefix, parent):
        self.parent = parent
        self.prefix = prefix

    def validate(self, name: str) -> ValidationResult:
        """"""
        valid, message = self.parent.run_local_validation(self.prefix)

        self.parent.update_input_tooltip(message, self.prefix)

        if valid:
            if self.prefix == "sub":
                # re-validate the ses in case the new sub has made it ok.
                self.parent.revalidate_inputs(["ses"])

            return self.success()
        else:
            return self.failure("")
