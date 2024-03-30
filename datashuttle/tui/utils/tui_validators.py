"""
Tools for live validation of user inputs in the DataShuttle TUI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datashuttle.tui.tabs.create_folders import CreateFoldersTab
    from datashuttle.utils.custom_types import Prefix

from textual.validation import ValidationResult, Validator


class NeuroBlueprintValidator(Validator):
    def __init__(self, prefix: Prefix, parent: CreateFoldersTab) -> None:
        """
        Custom Validator() class that takes
        sub / ses prefix as input. Runs validation of
        the name against the project and propagates
        any error message through the Input tooltip.
        """
        super(NeuroBlueprintValidator, self).__init__()
        self.parent = parent
        self.prefix = prefix

    def validate(self, name: str) -> ValidationResult:
        """
        Run validation and update the tooltip with the error,
        if no error then the formatted sub / ses name is displayed.
        This is set on an Input widget.
        """
        valid, message = self.parent.run_local_validation(self.prefix)

        self.parent.update_input_tooltip(message, self.prefix)

        if valid:
            if self.prefix == "sub":
                # re-validate the ses in case the new sub has made it ok.
                self.parent.revalidate_inputs(["ses"])

            return self.success()
        else:
            return self.failure("")
