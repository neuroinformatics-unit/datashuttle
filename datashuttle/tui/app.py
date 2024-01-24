from pathlib import Path

import yaml
from showinfm import show_in_file_manager
from textual.app import App
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import (
    Button,
    Label,
)

from datashuttle.configs import canonical_folders
from datashuttle.tui.screens import (
    modal_dialogs,
    new_project,
    project_manager,
    project_selector,
    settings,
)


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

    def on_mount(self):
        self.dark = self.load_global_settings()["dark_mode"]

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
                project_selector.ProjectSelectorScreen(self),
                self.load_project_page,
            )

        elif event.button.id == "mainwindow_new_project_button":
            self.push_screen(
                new_project.NewProjectScreen(self),
                self.load_project_page,
            )

        elif event.button.id == "mainwindow_settings_button":
            self.push_screen(
                settings.SettingsScreen(
                    self,
                )
            )

    def load_project_page(self, project):
        if project:
            self.push_screen(
                project_manager.ProjectManagerScreen(self, project)
            )

    def show_modal_error_dialog(self, message):
        self.push_screen(modal_dialogs.MessageBox(message, border_color="red"))

    def handle_open_filesystem_browser(self, path_):
        if not path_.exists():
            self.show_modal_error_dialog(
                f"{path_.as_posix()} cannto be opened as it "
                f"does not exist on the filesystem."
            )
            return

        try:
            show_in_file_manager(path_.as_posix())
        except BaseException:
            if path_.is_file():
                # I don't see why this is not working as according to docs it
                # should open the containing folder and select.
                message = (
                    "Could not open file. Only folders can be "
                    "opened in the filesystem browser."
                )
            else:
                message = (
                    "Unexpected error occurred. Please contact the DataShuttle"
                    "development team."
                )

            self.show_modal_error_dialog(message)

    def get_global_settings_path(self):
        path_ = canonical_folders.get_datashuttle_path()
        return path_ / "global_tui_settings.yaml"

    def load_global_settings(self):
        # TODO: there is now a lot of code that does this kind of thing
        # here, persistent settings, configs. See if it can be centralised
        settings_path = self.get_global_settings_path()

        if not settings_path.is_file():
            global_settings = {
                "dark_mode": True,
                "show_transfer_tree_status": False,
            }
            self.save_global_settings(global_settings)
        else:
            with open(settings_path, "r") as file:
                global_settings = yaml.full_load(file)

        return global_settings

    def save_global_settings(self, global_settings):
        settings_path = self.get_global_settings_path()

        with open(settings_path, "w") as file:
            yaml.dump(global_settings, file, sort_keys=False)


if __name__ == "__main__":
    TuiApp().run()
