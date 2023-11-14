from time import monotonic
from typing import Optional

from textual.containers import Horizontal
from textual.validation import ValidationResult, Validator
from textual.widgets import (
    Button,
    DirectoryTree,
    Input,
    Label,
    TabPane,
)

from datashuttle.tui import custom_widgets
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

        # TODO: move
        self.default_input_tooltip = ""

    def compose(self):
        yield DirectoryTree(
            self.project.cfg.data["local_path"],
            id="tabscreen_directorytree",
        )
        yield Label("Subject(s)", id="tabscreen_subject_label")
        yield Input(
            id="tabscreen_subject_input",
            placeholder="e.g. sub-001",
            validate_on=["changed", "submitted"],
            validators=[QuickNeuroBlueprintValidator("sub", self)],
        )  # TODO: what is validate_on["blur"]?
        yield Label("Session(s)", id="tabscreen_session_label")
        yield Input(
            id="tabscreen_session_input",
            placeholder="e.g. ses-001",
            validate_on=["changed", "submitted"],
            validators=[QuickNeuroBlueprintValidator("ses", self)],
        )
        yield Label("Datatype(s)", id="tabscreen_datatype_label")
        yield custom_widgets.DatatypeCheckboxes(self.project)
        yield Horizontal(
            Button("Make Folders", id="tabscreen_make_folder_button"),
            Button("Create Options", id="tabscreen_create_options_button"),
        )

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ):
        """
        Upon double-clicking a directory within the directory-tree
        widget, replace contents of the \'Subject\' and/or \'Session\'
        input widgets, depending on the prefix of the directory selected.
        Double-click time is set to the Windows default duration (500 ms).
        """
        click_time = monotonic()
        if click_time - self.prev_click_time < 0.5:
            if event.path.stem.startswith("sub-"):
                self.query_one("#tabscreen_subject_input").value = str(
                    event.path.stem
                )
            if event.path.stem.startswith("ses-"):
                self.query_one("#tabscreen_session_input").value = str(
                    event.path.stem
                )
        self.prev_click_time = click_time

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
                    datatype=self.query_one("DatatypeCheckboxes").type_out,
                )
                self.query_one("#tabscreen_directorytree").reload()
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return

    def run_local_validation(self, prefix):
        """ """
        try:
            sub_dir = self.query_one("#tabscreen_subject_input").value

            format_sub = formatting.check_and_format_names([sub_dir], "sub")

            if prefix == "sub":
                format_ses = None
            else:
                ses_dir = self.query_one("#tabscreen_session_input").value

                format_ses = formatting.check_and_format_names(
                    [ses_dir], "ses"
                )

            validation.validate_names_against_project(
                self.project.cfg,
                format_sub,
                format_ses,
                local_only=True,
                error_or_warn="error",
                log=False,
            )

        except Exception as e:
            return False, str(e)

        return True, "No issues detected"

    def update_input_tooltip(self, message: Optional[str], prefix):
        """ """
        id = (
            "#tabscreen_subject_input"
            if prefix == "sub"
            else "#tabscreen_session_input"
        )
        input = self.query_one(id)
        input.tooltip = message


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
                value = self.parent.query_one("#tabscreen_session_input").value
                self.parent.query_one("#tabscreen_session_input").validate(
                    value=value
                )

            return self.success()
        else:
            return self.failure("")


# it is allowing double keys, if not prefix
# ses-a etc is not checked for sub name...
# weird focus on
