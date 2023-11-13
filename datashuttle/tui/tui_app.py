from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import (
    Button,
    Label,
)

from datashuttle.tui import (
    project_config,
    project_select,
)
from datashuttle.tui.screens import modal_dialogs, project_manager

# RENAME ALL WIDGETS
# TCSS


class TuiApp(App):
    """
    The main app page for the DataShuttle TUI.

    This class acts as a base class from which all windows
    (select existing project, make new project, settings and
    get help) are raised.

    Running this application in a main block as below
    if __name__ == __main__:
         app = MyApp()
         app.run()

    Initialises the TUI event loop and starts the application.
    """

    tui_path = Path(__file__).parent
    CSS_PATH = list(Path(tui_path / "css").glob("*.tcss"))

    BINDINGS = [
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    def compose(self):
        yield Container(
            Label("DataShuttle", id="mainwindow_banner_label"),
            Button(
                "Select Existing Project",
                id="mainwindow_existing_project_button",
            ),
            Button("Make New Project", id="mainwindow_new_project_button"),
            Button("Settings", id="mainwindow_settings_button"),
            Button("Get Help", id="mainwindow_get_help_button"),
            id="mainwindow_contents_container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        """
        When a button is pressed, a new screen is displayed with
        `push_screen`. The second argument is a callback to
        load the project page, with an initialised project
        or `None` (in case no project was selected).

        Error handling is at the level of the individual screens,
        but presentation of the error dialog is handled in
        `self.show_modal_error_dialog()`.
        """
        if event.button.id == "mainwindow_existing_project_button":
            self.push_screen(
                project_select.ProjectSelector(self), self.load_project_page
            )

        elif event.button.id == "mainwindow_new_project_button":
            self.push_screen(
                project_config.NewProjectScreen(self),
                self.load_project_page,
            )

    def load_project_page(self, project):
        if project:
            self.push_screen(
                project_manager.ProjectManagerScreen(self, project)
            )

    def show_modal_error_dialog(self, message):
        self.push_screen(modal_dialogs.ErrorScreen(message))


if __name__ == "__main__":
    TuiApp().run()
