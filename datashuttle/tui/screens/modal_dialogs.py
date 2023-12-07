from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Label, Static


class ErrorScreen(ModalScreen):
    """
    A screen for rendering error messages. The border of the
    central widget is red. The screen does not return any value.
    """

    def __init__(self, message):
        super(ErrorScreen, self).__init__()

        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Static(self.message, id="errorscreen_message_label"),
                id="errorscreen_message_container",
            ),
            Container(Button("OK"), id="errorscreen_ok_button"),
            id="errorscreen_top_container",
        )

    def on_button_pressed(self) -> None:
        self.dismiss()


class ShowConfigsDialog(ModalScreen):
    """
    This window is used to display the configs of a newly (re-)configured
    project. The message above the displayed configs can be configured
    depending on whether a new project was created or an existing project
    was updated.

    This screen returns None, such that it is displayed until the
    user presses OK via a callback function. See
    `ConfigsContent.setup_configs_for_a_new_project_and_switch_to_tab_screen()`
    for more information.
    """

    def __init__(self, project_configs_dict, message_before_dict=""):
        super(ShowConfigsDialog, self).__init__()

        self.project_configs_dict = project_configs_dict
        self.message_before_dict = message_before_dict

    def compose(self):
        yield Container(
            Container(
                Static(
                    self.message_before_dict,
                    id="display_configs_message_label",
                ),
                DataTable(id="modal_table", show_header=False),
                id="display_configs_message_container",
            ),
            Container(Button("OK"), id="display_configs_ok_button"),
            id="display_configs_top_container",
        )

    def on_mount(self):
        """
        The first row is empty because the header is not displayed.
        """
        ROWS = [("", "")] + [
            (key, value) for key, value in self.project_configs_dict.items()
        ]

        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])

        for row in ROWS[1:]:
            styled_row = [Text(str(cell), justify="left") for cell in row]
            table.add_row(*styled_row)

    def on_button_pressed(self) -> None:
        self.dismiss(None)


class ConfirmScreen(ModalScreen):
    """
    A screen for rendering confirmation messages.
    """

    def __init__(self, message):
        super().__init__()

        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.message, id="confirm_message_label"),
            Horizontal(
                Button("Yes", id="confirm_ok_button"),
                Button("No", id="confirm_cancel_button"),
                id="confirm_button_container",
            ),
            id="confirm_top_container",
        )

    def on_button_pressed(self, event) -> None:
        if event.button.id == "confirm_ok_button":
            self.dismiss(True)
        else:
            self.dismiss(False)
