from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Header

from datashuttle import DataShuttle
from datashuttle.utils.getters import get_existing_project_paths


class ProjectSelectorScreen(Screen):
    """
    The project selection screen. Finds and displays DataShuttle
    projects present on the local system.

    `self.dismiss()` returns an initialised project if initialisation
    was successful. Otherwise, in case `Main Menu` button is pressed,
    returns None to return without effect to the main menu.,

    Parameters
    ----------

    mainwindow : TuiApp
        The main TUI app, functions on which are used to coordinate
        screen display.

    """

    TITLE = "Select Project"

    def __init__(self, mainwindow):
        super(ProjectSelectorScreen, self).__init__()

        self.project_names = [
            path_.stem for path_ in get_existing_project_paths()
        ]
        self.mainwindow = mainwindow

    def compose(self):
        yield Header(id="project_select_header")
        yield Button("Main Menu", id="all_main_menu_buttons")
        yield Container(
            *[Button(name, id=name) for name in self.project_names],
            id="project_select_top_container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id in self.project_names:
            try:
                project = DataShuttle(str(event.button.id))
            except BaseException as e:
                self.mainwindow.show_modal_error_dialog(str(e))
                return
            self.dismiss(project)

        elif event.button.id == "all_main_menu_buttons":
            self.dismiss(False)
