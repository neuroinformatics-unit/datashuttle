from __future__ import annotations

from typing import TYPE_CHECKING, Dict

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

    def __init__(self, project, transfer_checkboxes=False):
        super(DatatypeCheckboxes, self).__init__()

        self.project = project
        self.datatype_config = get_datatypes()
        self.transfer_checkboxes = transfer_checkboxes
        if transfer_checkboxes:
            self.datatype_config.extend(
                ["all", "all_datatype", "all_ses_level_non_datatype"]
            )
        self.persistent_settings = self.project._load_persistent_settings()

    def compose(self):
        checkboxes_on = self.persistent_settings["tui"]["checkboxes_on"]

        if self.transfer_checkboxes:
            checkboxes_on.update(
                {
                    "all": True,
                    "all_datatype": True,
                    "all_ses_level_non_datatype": True,
                }
            )  # TODO: handle!

        for datatype in self.datatype_config:
            #      assert False, f"{self.transfer_checkboxes}-{self.datatype_config}"

            assert (
                datatype in checkboxes_on.keys()
            ), "Need to update tui persistent settings."

            yield Checkbox(
                datatype.title(),
                id=f"tabscreen_{datatype}_checkbox",
                value=checkboxes_on[datatype],
            )

    def on_mount(self):
        """
        Update datatype out based on the current checkbox
        ticks which are determined during `compose().`
        """
        datatype_dict = self.get_datatype_dict()
        self.set_datatype_out(datatype_dict)

    def on_checkbox_changed(self):
        """
        When a checkbox is clicked, update the `datatype_out` attribute
        with the datatypes to pass to `make_folders` datatype argument.
        """
        datatype_dict = self.get_datatype_dict()

        # This is slightly wasteful as update entire dict instead
        # of changed entry, but is negligible.
        self.persistent_settings["tui"]["checkboxes_on"] = datatype_dict

        self.project._save_persistent_settings(self.persistent_settings)

        self.set_datatype_out(datatype_dict)

    def get_datatype_dict(self) -> Dict:
        """"""
        datatype_dict = {
            datatype: self.query_one(f"#tabscreen_{datatype}_checkbox").value
            for datatype in self.datatype_config
        }

        return datatype_dict

    def set_datatype_out(self, datatype_dict: dict) -> None:
        """"""
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
