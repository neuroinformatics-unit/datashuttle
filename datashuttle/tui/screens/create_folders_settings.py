from typing import Literal

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    RadioButton,
    RadioSet,
    Static,
)


class TemplateSettingsScreen(ModalScreen):  # TODO: figure out modal_dialogs.py
    TITLE = "Template Settings"

    def __init__(self, mainwindow, project):
        super(TemplateSettingsScreen, self).__init__()  # TODO: think on naming

        self.mainwindow = mainwindow
        self.input_mode: Literal["sub", "ses"] = "sub"
        self.project = project

        self.templates = self.project.get_name_templates()

    # assert False, f"{self.templates}"

    def compose(self):
        sub_on = True if self.input_mode == "sub" else False
        ses_on = not sub_on

        explanation = """
        Set a template subject or session name
        that can be auto-filled on the create folders
        name input boxes.

        TODO: add a link to documentation. Allow \d\d, ??, *
        """
        yield Container(
            Horizontal(
                Static(explanation, id="template_message_label"),
                id="test_container",
            ),
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
            Button("Close", id="template_sessions_close_button"),
            id="template_top_container",
        )

    def on_mount(self):
        # TODO: own function
        input = self.query_one("#template_settings_input")
        value = self.templates[self.input_mode]
        if value is None:
            input.placeholder = f"{self.input_mode}-"
        else:
            input.value = value

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "template_sessions_close_button":
            self.dismiss(self.templates)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        Update the displayed SSH widgets when the `connection_method`
        radiobuttons are changed.
        """
        label = str(event.pressed.label)
        assert label in ["Subject", "Session"], "Unexpected label."
        self.input_mode = "sub" if label == "Subject" else "ses"

        # TODO own function
        input = self.query_one("#template_settings_input")
        value = self.templates[self.input_mode]

        if value:
            input.value = value
        else:
            input.value = ""
            input.placeholder = f"{self.input_mode}-"

    def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id == "template_settings_input":
            self.templates[self.input_mode] = message.value
