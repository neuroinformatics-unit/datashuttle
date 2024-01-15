from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from textual import events

from dataclasses import dataclass

from textual.message import Message
from textual.widgets import Checkbox, Input, Static


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

    def get_selected_datatypes(self) -> List[str]:
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
