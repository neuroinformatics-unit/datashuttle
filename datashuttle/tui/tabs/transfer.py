from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    DirectoryTree,
    Input,
    Label,
    RadioButton,
    RadioSet,
    TabPane,
)

from datashuttle.tui.custom_widgets import DatatypeCheckboxes
from datashuttle.tui.utils.tui_validators import NeuroBlueprintValidator


class TransferTab(TabPane):
    def __init__(self, mainwindow, project):
        super(TransferTab, self).__init__(
            "Transfer", id="tabscreen_transfer_tab"
        )
        self.mainwindow = mainwindow
        self.project = project

    def compose(self):
        self.transfer_all_widgets = [  # TODO: Check if rawdata and derivatives can have different names?
            Label(
                "All data from: \n\n - Rawdata \n - Derivatives \n\nWill be transferred."
                " Existing data with \nthe same file details on central will not be \noverwritten.",
                id="transfer_all_label",
            )
        ]

        self.transfer_toplevel_widgets = [
            Label(
                "Double-click file tree to choose top-level \nfolder to transfer",
                id="transfer_toplevel_label_top",
            ),
            Input(
                value="Placeholder",
                disabled=True,
                id="transfer_toplevel_input",
            ),
            Label(
                "Existing data with the same file details on \ncentral will not be overwritten by default."
            ),
        ]

        self.transfer_custom_widgets = [
            Label("Subject(s)", id="tabscreen_subject_label"),
            Input(
                id="tabscreen_subject_input",
                placeholder="e.g. sub-001",
                validate_on=["changed", "submitted"],
                validators=[NeuroBlueprintValidator("sub", self)],
            ),
            Label("Session(s)", id="tabscreen_session_label"),
            Input(
                id="tabscreen_session_input",
                placeholder="e.g. ses-001",
                validate_on=["changed", "submitted"],
                validators=[NeuroBlueprintValidator("ses", self)],
            ),
            Label("Datatype(s)", id="tabscreen_datatype_label"),
            DatatypeCheckboxes(self.project),
        ]

        yield DirectoryTree(
            self.project.cfg.data["local_path"],
            id="tabscreen_directorytree",
        )
        yield RadioSet(
            RadioButton("All", id="transfer_all_radiobutton", value=True),
            RadioButton("Top Level", id="transfer_toplevel_radiobutton"),
            RadioButton("Custom", id="transfer_custom_radiobutton"),
            id="transfer_radioset",
        )
        yield Container(
            *self.transfer_all_widgets,
            *self.transfer_toplevel_widgets,
            *self.transfer_custom_widgets,
            id="transfer_params_container",
        )
        yield Horizontal(
            Button("Transfer"),
            Button("Options"),
        )

    def on_mount(self):
        self.query_one(
            "#transfer_params_container"
        ).border_title = "Parameters"
        self.switch_transfer_widgets_display(display_bool=[True, False, False])

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """
        Update the displayed transfer parameter widgets when the
        `transfer_radioset` radiobuttons are changed.
        """
        label = str(event.pressed.label)
        assert label in ["All", "Top Level", "Custom"], "Unexpected label."
        display_bool = [
            self.query_one("#transfer_all_radiobutton").value,
            self.query_one("#transfer_toplevel_radiobutton").value,
            self.query_one("#transfer_custom_radiobutton").value,
        ]
        self.switch_transfer_widgets_display(display_bool)

    def switch_transfer_widgets_display(self, display_bool):
        """
        Show or hide transfer parameters based on whether the transfer mode
        currently selected in `transfer_radioset`.
        """
        for widget in self.transfer_all_widgets:
            widget.display = display_bool[0]

        for widget in self.transfer_toplevel_widgets:
            widget.display = display_bool[1]

        for widget in self.transfer_custom_widgets:
            widget.display = display_bool[2]
