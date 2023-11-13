from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Button,
    Header,
    TabbedContent,
    TabPane,
)

from datashuttle.tui import project_config
from datashuttle.tui.tabs import create_tab, transfer_tab


class TabScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.

    The 'Create' tab interacts with Datashuttle's `make_folders()`
    method to create new project folders.

    The 'Transfer' tab, XXX.

    The 'Configs' tab displays the current project's configurations
    and allows configs to be reset. This is an instantiation of the
    ConfigsContent window, which is also shared by `Make New Project`.
    See ConfigsContent for more information.

    Parameters
    ----------

    mainwindow : TuiApp
        The main application window used for coordinating screen display.

    project : DataShuttle
        An instantiated datashuttle project.
    """

    def __init__(self, mainwindow, project):
        super(TabScreen, self).__init__()

        self.mainwindow = mainwindow
        self.project = project
        self.title = f"Project: {self.project.project_name}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Main Menu", id="all_main_menu_buttons")
        with TabbedContent(
            id="tabscreen_tabbed_content", initial="tabscreen_create_tab"
        ):
            yield create_tab.CreateTab(self.mainwindow, self.project)
            yield transfer_tab.TransferTab(self.mainwindow, self.project)
            with TabPane("Configs", id="tabscreen_configs_tab"):
                yield project_config.ConfigsContent(self, self.project)

    def on_button_pressed(self, event: Button.Pressed):
        """
        Dismisses the TabScreen (and returns to the main menu) once
        the 'Main Menu' button is pressed.
        """

        if event.button.id == "all_main_menu_buttons":
            self.dismiss()
