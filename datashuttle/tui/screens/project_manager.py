from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Button,
    Header,
    TabbedContent,
    TabPane,
)

from datashuttle.tui import configs
from datashuttle.tui.tabs import create_folders, transfer


class ProjectManagerScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.

    The 'Create' tab interacts with Datashuttle's `make_folders()`
    method to create new project folders.

    The 'Transfer' tab, which handles data upload and download between
    local / central.

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
        super(ProjectManagerScreen, self).__init__()

        self.mainwindow = mainwindow
        self.project = project
        self.title = f"Project: {self.project.project_name}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Main Menu", id="all_main_menu_buttons")
        with TabbedContent(
            id="tabscreen_tabbed_content", initial="tabscreen_create_tab"
        ):
            yield create_folders.CreateFoldersTab(
                self.mainwindow, self.project
            )
            yield transfer.TransferTab(
                "Transfer",
                self.mainwindow,
                self.project,
                id="tabscreen_transfer_tab",
            )
            with TabPane("Configs", id="tabscreen_configs_tab"):
                yield configs.ConfigsContent(self, self.project)

    def on_button_pressed(self, event: Button.Pressed):
        """
        Dismisses the TabScreen (and returns to the main menu) once
        the 'Main Menu' button is pressed.
        """
        if event.button.id == "all_main_menu_buttons":
            self.dismiss()

    def on_tabbed_content_tab_activated(self, event):
        """
        Refresh the directorytree for create or transfer tabs whenever
        the tabbedcontent is switched to one of these tabs.
        """
        if event.pane.id == "tabscreen_create_tab":
            self.query_one("#tabscreen_create_tab").reload_directorytree()
        elif event.pane.id == "tabscreen_transfer_tab":
            self.query_one("#tabscreen_transfer_tab").reload_directorytree()
