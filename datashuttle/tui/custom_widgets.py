from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual import events

from dataclasses import dataclass

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Checkbox, Input, Static

from datashuttle.configs.canonical_configs import get_datatypes


class DatatypeCheckboxes(Static):
    """
    Dynamically-populated checkbox widget for convenient datatype
    selection during folder creation.

    Attributes
    ----------

    datatype_out:
        List of datatypes selected by the user to be passed to `make_folders`
        (e.g. "behav" that will be passed to `make-folders`.)

    type_config:
        List of datatypes supported by NeuroBlueprint
    """

    datatype_out = reactive("all")

    def __init__(self, project):
        super(DatatypeCheckboxes, self).__init__()

        self.project = project
        self.datatype_config = get_datatypes()
        self.persistent_settings = self.project._load_persistent_settings()

    def compose(self):
        checkboxes_on = self.persistent_settings["tui"]["checkboxes_on"]

        for datatype in self.datatype_config:
            assert datatype in checkboxes_on.keys(), (
                "Need to update tui" "persistent settings."
            )

            yield Checkbox(
                datatype.title(),
                id=f"tabscreen_{datatype}_checkbox",
                value=checkboxes_on[datatype],
            )

    def on_checkbox_changed(self):
        """
        When a checkbox is clicked, update the `datatype_out` attribute
        with the datatypes to pass to `make_folders` datatype argument.
        """
        datatype_dict = {
            datatype: self.query_one(f"#tabscreen_{datatype}_checkbox").value
            for datatype in self.datatype_config
        }

        # This is slightly wasteful as update entire dict instead
        # of changed entry, but is negligible.
        self.persistent_settings["tui"]["checkboxes_on"] = datatype_dict

        self.project._save_persistent_settings(self.persistent_settings)

        self.datatype_out = [
            datatype
            for datatype, is_on in zip(
                datatype_dict.keys(), datatype_dict.values()
            )
            if is_on
        ]


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
