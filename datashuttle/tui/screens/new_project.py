from textual.screen import Screen
from textual.widgets import Button, Header

from datashuttle.tui import configs


class NewProjectScreen(Screen):
    """
    Screen for setting up a new datashuttle project, by
    inputting the desired configs. This uses the
    ConfigsContent window to display and set the configs.

    If "Main Manu" button is pressed, the callback function
    returns None, so the project screen is not switched to.

    Otherwise, the logic for creating and validating the
    project is in ConfigsContent. ConfigsContent calls
    the dismiss method of this class to return
    an initialised project to mainwindow.
    See ConfigsContent.on_button_pressed() for more details

    Parameters
    ----------

    mainwindow : TuiApp
    """

    TITLE = "Make New Project"

    def __init__(self, mainwindow):
        super(NewProjectScreen, self).__init__()

        self.mainwindow = mainwindow

    def compose(self):
        yield Header()
        yield Button("Main Menu", id="all_main_menu_buttons")
        yield configs.ConfigsContent(self, project=None)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "all_main_menu_buttons":
            self.dismiss(None)
