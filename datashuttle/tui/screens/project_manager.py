from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Button,
    Header,
    TabbedContent,
    TabPane,
)

from datashuttle.tui.configs import ConfigsContent
from datashuttle.tui.tabs import create_folders, transfer


class ProjectManagerScreen(Screen):
    """
    Screen containing the Create and Transfer tabs. This is
    the primary screen within which the user interacts with
    a pre-configured project.

    The 'Create' tab interacts with Datashuttle's `create_folders()`
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

        # see `on_tabbed_content_tab_activated()`
        self.tabbed_content_mount_signal = True

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
                yield ConfigsContent(self, self.project)

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

        This is also triggered on mount, leading to it being reloaded
        twice, leading to a strange flicker. Ideally no trigger
        would be sent on mount. Therefore the ugly `tabbed_content_mount_signal`
        variable is introduced to track this.
        """
        if self.tabbed_content_mount_signal:
            self.tabbed_content_mount_signal = False
            return

        if event.pane.id == "tabscreen_create_tab":
            self.query_one("#tabscreen_create_tab").reload_directorytree()
        elif event.pane.id == "tabscreen_transfer_tab":
            self.query_one("#tabscreen_transfer_tab").reload_directorytree()

    def on_configs_content_configs_saved(self):
        """
        When the config file are refreshed, the local path may have changed.
        In this case the directorytree will be displaying the wrong root,
        so update it here.

        TODO
        ----
        Currently this defaults to the local path always but in future when it
        shows the central path it will have to be updated.
        """
        self.query_one("#tabscreen_create_tab").update_directorytree_root(
            self.project.cfg["local_path"]
        )
        self.query_one("#tabscreen_transfer_tab").update_directorytree_root(
            self.project.cfg["local_path"]
        )
