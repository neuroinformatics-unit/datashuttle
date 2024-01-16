from __future__ import annotations

from typing import List, Optional

from textual import on
from textual.containers import Horizontal
from textual.widgets import (
    Button,
    DirectoryTree,
    Label,
    TabPane,
)

from datashuttle.tui.custom_widgets import (
    ClickableInput,
    CustomDirectoryTree,
    DatatypeCheckboxes,
)
from datashuttle.tui.screens.template_settings import (
    TemplateSettingsScreen,
)
from datashuttle.tui.utils.tui_decorators import require_double_click
from datashuttle.tui.utils.tui_validators import NeuroBlueprintValidator
from datashuttle.utils import formatting, validation


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
        yield CustomDirectoryTree(
            self.project.cfg.data["local_path"],
            id="tabscreen_directorytree",
        )
        yield Label("Subject(s)", id="tabscreen_subject_label")
        yield ClickableInput(
            id="tabscreen_subject_input",
            placeholder="e.g. sub-001",
            validate_on=["changed", "submitted"],
            validators=[NeuroBlueprintValidator("sub", self)],
        )
        yield Label("Session(s)", id="tabscreen_session_label")
        yield ClickableInput(
            id="tabscreen_session_input",
            placeholder="e.g. ses-001",
            validate_on=["changed", "submitted"],
            validators=[NeuroBlueprintValidator("ses", self)],
        )
        yield Label("Datatype(s)", id="tabscreen_datatype_label")
        yield DatatypeCheckboxes(self.project)
        yield Horizontal(
            Button("Make Folders", id="tabscreen_make_folder_button"),
            Button(
                "Template Settings", id="tabscreen_template_settings_button"
            ),
        )

    @on(ClickableInput.Clicked)
    @require_double_click
    def handle_input_click(self, event: ClickableInput.Clicked) -> None:
        """
        Handled a double-click on the custom ClickableInput widget.
        Determine if we have the subject or session input, and
        if it was a left or right click. Then, fill with a either
        a generic suggestion or suggestion based on next sub / ses number.
        """
        input_id = event.input.id

        assert input_id in [
            "tabscreen_session_input",
            "tabscreen_subject_input",
        ], "unknown input name"

        prefix = "sub" if "subject" in input_id else "ses"

        if event.button == 1:
            self.fill_input_with_template(prefix, input_id)
        elif event.button == 3:
            self.fill_input_with_next_sub_or_ses_template(prefix, input_id)

    def fill_input_with_template(self, prefix, input_id):
        """
        Given the `name_template` stored in `self.templates`,
        fill the sub or ses Input with the template (based on `prefix`).
        If `self.templates` is off, then just suggest "sub-" or "ses-".
        """
        if self.templates["on"] and self.templates[prefix] is not None:
            fill_value = self.templates[prefix]
        else:
            fill_value = f"{prefix}-"

        input = self.query_one(f"#{input_id}")
        input.value = fill_value

    def fill_input_with_next_sub_or_ses_template(self, prefix, input_id):
        """
        This fills a sub / ses Input with a suggested name based on the
        next subject / session in the project (local).

        If `name_templates` are set, then the sub- or ses- first key
        of the template name will be replaced with the suggested
        sub or ses key-value. Otherwise, the sub/ses key-value pair only
        will be suggested.

        Parameters

        prefix : Literal["sub", "ses"]
            Whether to fill the subject or session Input

        input_id : str
            The textual input name to update.
        """
        if prefix == "sub":
            next_val = self.project.get_next_sub_number(
                return_with_prefix=True, local_only=True
            )
        else:
            sub_names = self.query_one(
                "#tabscreen_subject_input"
            ).as_names_list()

            if len(sub_names) > 1:
                self.mainwindow.show_modal_error_dialog(
                    "Can only suggest next session number when a "
                    "single subject is provided."
                )
                return
            else:
                sub = sub_names[0]

            next_val = self.project.get_next_ses_number(
                sub, return_with_prefix=True, local_only=True
            )
        if self.templates["on"] and self.templates[prefix] is not None:
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
        if event.path.stem.startswith("sub-"):
            self.query_one("#tabscreen_subject_input").value = str(
                event.path.stem
            )
        if event.path.stem.startswith("ses-"):
            self.query_one("#tabscreen_session_input").value = str(
                event.path.stem
            )

    def on_button_pressed(self, event: Button.Pressed):
        """
        Enables the Make Folders button to read out current input values
        and use these to call project.make_folders().
        """
        if event.button.id == "tabscreen_make_folder_button":
            sub_names = self.query_one(
                "#tabscreen_subject_input"
            ).as_names_list()
            ses_names = self.query_one(
                "#tabscreen_session_input"
            ).as_names_list()
            datatype = self.query_one(
                "DatatypeCheckboxes"
            ).selected_datatypes()

            if ses_names == [""]:
                ses_names = None

            try:
                self.project.make_folders(
                    sub_names=sub_names, ses_names=ses_names, datatype=datatype
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
        """
        Run validation of the values stored in the
        sub / ses Input according to the passed prefix
        using core datashuttle functions.

        First, format the subject name (and session if required)
        which also performs quick name format validations. Then,
        compare the names against all current project sub / names (local)
        and check it is valid. If invalid, the functions will error
        and the error is caught and message returned. Otherwise,
        the formatted name is returned.

        TODO
        ----
        This basically mirrors the validation done in `make_folders()`.
        There is scope for divergence in the logic of these two pathways.
        This can be resolved by carefully testing their outputs or
        ensuring the same code is used underlying both. It is close
        because both call `check_and_format_names` but could be tighter.
        """
        try:
            sub_names = self.query_one(
                "#tabscreen_subject_input"
            ).as_names_list()

            format_sub = formatting.check_and_format_names(
                sub_names, "sub", name_templates=self.templates
            )

            if prefix == "sub":
                format_ses = None
            else:
                ses_names = self.query_one(
                    "#tabscreen_session_input"
                ).as_names_list()

                format_ses = formatting.check_and_format_names(
                    ses_names, "ses", name_templates=self.templates
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
        """"""
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
