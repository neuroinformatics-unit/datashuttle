import webbrowser

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    RadioButton,
    RadioSet,
)

from datashuttle.tui.custom_widgets import TopLevelFolderSelect


class CreateFoldersSettingsScreen(ModalScreen):
    """
    This screen handles setting datashuttle's `name_template`'s, as well
    as the top-level-folder select and option to bypass all validation.

    Name Templates
    --------------
    These are regexp templates that can be validated against
    during folder creation / project validation.

    An input is provided to input a `name_template` for validation. When
    the window is closed, the `name_template` is stored in datashuttle's
    persistent settings.

    The Create tab validation on Inputs is immediately updated on closing
    of this screen.
    """

    TITLE = "Create Folders Settings"

    def __init__(self, mainwindow, project):
        super(CreateFoldersSettingsScreen, self).__init__()

        self.mainwindow = mainwindow
        self.input_mode = "sub"
        self.project = project

        self.templates = self.project.get_name_templates()

    def action_link_docs(self) -> None:
        webbrowser.open("https://datashuttle.neuroinformatics.dev/")

    def compose(self):
        sub_on = True if self.input_mode == "sub" else False
        ses_on = not sub_on

        explanation = """
        A 'Template' can be set check subject or session names are
        formatted in a specific way.

        For example:
            sub-\d\d_id-.?.?.?_.*

        Visit the [@click=screen.link_docs()]Documentation[/] for more information.
        """

        bypass_validation = self.project.get_bypass_validation()

        yield Container(
            Horizontal(
                Label("Top level folder:", id="labelTESTEST"),
                TopLevelFolderSelect(
                    self.project,
                    existing_only=True,
                    id="create_folders_settings_toplevel_select",
                ),
            ),
            Checkbox(
                "Bypass validation",
                value=bypass_validation,
                id="create_folders_settings_bypass_validation_checkbox",
            ),
            Container(
                Horizontal(
                    Checkbox(
                        "Template Validation",
                        id="template_settings_validation_on_checkbox",
                        value=self.templates["on"],
                    ),
                    id="template_inner_horizontal_container",
                ),
                Container(
                    Label(explanation, id="template_message_label"),
                    Container(
                        RadioSet(
                            RadioButton(
                                "Subject",
                                id="template_settings_subject_radiobutton",
                                value=sub_on,
                            ),
                            RadioButton(
                                "Session",
                                id="template_settings_session_radiobutton",
                                value=ses_on,
                            ),
                            id="template_settings_radioset",
                        ),
                        Input(id="template_settings_input"),
                        id="template_other_widgets_container",
                    ),
                    id="template_inner_container",
                ),
                id="template_top_container",
            ),
            Container(),
            Button("Close", id="create_folders_settings_close_button"),
            id="template_top_container2",
        )

    def on_mount(self):
        self.fill_input_from_template()
        self.set_disabled_mode_widgets()

    def set_disabled_mode_widgets(self):
        """
        When `self.templates["on"]` is `False`, all
        template widgets are disabled.
        """
        cont = self.query_one("#template_inner_container")
        cont.disabled = not self.templates["on"]

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create_folders_settings_close_button":
            self.dismiss(self.templates)
        elif event.button.id == "create_settings_bypass_validation_button":
            self.project.set_bypass_validation(on=False)

    def on_checkbox_changed(self, event):
        """
        Turn `name_templates` on or off and update the TUI accordingly.
        """
        is_on = event.value

        if event.checkbox.id == "template_settings_validation_on_checkbox":
            self.templates["on"] = is_on
            self.project.set_name_templates(self.templates)
            self.set_disabled_mode_widgets()

        elif (
            event.checkbox.id
            == "create_folders_settings_bypass_validation_checkbox"
        ):
            self.project.set_bypass_validation(on=is_on)
            self.query_one("#template_inner_container").disabled = is_on
            self.query_one(
                "#template_settings_validation_on_checkbox"
            ).disabled = is_on

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        Update the displayed SSH widgets when the `connection_method`
        radiobutton's are changed.
        """
        label = str(event.pressed.label)
        assert label in ["Subject", "Session"], "Unexpected label."
        self.input_mode = "sub" if label == "Subject" else "ses"

        self.fill_input_from_template()

    def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id == "template_settings_input":
            self.templates[self.input_mode] = message.value

    def fill_input_from_template(self):
        input = self.query_one("#template_settings_input")
        value = self.templates[self.input_mode]

        if value is None:
            input.placeholder = f"{self.input_mode}-"
        else:
            input.value = value
