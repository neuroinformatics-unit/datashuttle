from typing import Literal

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
        A 'Template' can be set check subject or
        session names are formatted in a specific way.

        For example:
            sub-\d\d_id-.?.?.?_.*

        Visit my [link=https://www.willmcgugan.com]blog[/link]! for more information.
        """
        yield Container(
            Horizontal(
                Checkbox(
                    "Template Validation",
                    id="template_settings_validation_on_checkbox",
                    value=self.templates["on"],
                ),
                Horizontal(),
                Button("Close", id="template_sessions_close_button"),
                id="template_inner_horizontal_container",
            ),
            Container(
                Container(
                    Label(explanation, id="template_message_label"), id="test3"
                ),
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
                    id="test4",
                ),
                id="template_inner_container",
            ),
            id="template_top_container",
        )

    # TODO: tooltip on input widget.

    def on_mount(self):
        container = self.query_one("#template_top_container")
        container.border_title = "Template Settings"

        # TODO: own function
        input = self.query_one("#template_settings_input")
        value = self.templates[self.input_mode]
        if value is None:
            input.placeholder = f"{self.input_mode}-"
        else:
            input.value = value

        self.set_disabled_mode_widgets()

    def set_disabled_mode_widgets(self):
        """"""
        cont = self.query_one("#template_inner_container")
        cont.disabled = not self.templates["on"]

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "template_sessions_close_button":
            self.dismiss(self.templates)

    def on_checkbox_changed(self, message):
        is_on = message.value

        self.templates["on"] = is_on
        self.project.set_name_templates(self.templates)
        self.set_disabled_mode_widgets()

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
