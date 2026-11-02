from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widget import Widget

    from datashuttle.tui.app import TuiApp

from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Header,
    Label,
    Static,
)

from datashuttle.datashuttle_functions import (
    _permanent_delete_project_files,
    empty_trash,
    get_deleted_projects,
    restore_project_from_trash,
)
from datashuttle.tui.screens import modal_dialogs


class RecycleBinScreen(Screen):
    """The Recycle Bin screen.

    Displays soft-deleted projects that are in the 30-day retention period.
    Users can restore projects back to active status, permanently delete
    specific projects with typed confirmation, or empty the entire Recycle Bin.
    """

    TITLE = "Recycle Bin"

    def __init__(self, mainwindow: TuiApp) -> None:
        """Initialise the RecycleBinScreen."""
        super(RecycleBinScreen, self).__init__()
        self.mainwindow = mainwindow
        self.deleted_projects: List[Dict] = []

    def compose(self) -> ComposeResult:
        """Add widgets to the RecycleBinScreen."""
        yield Header(id="recycle_bin_header")
        yield Button("Main Menu", id="all_main_menu_buttons")

        self.deleted_projects = get_deleted_projects()

        items_widgets: List[Widget] = []
        if not self.deleted_projects:
            items_widgets.append(
                Static(
                    "The Recycle Bin is empty.\n\n"
                    "When projects are deleted, they will be kept here for 30 days before automatic removal.",
                    id="recycle_bin_empty_label",
                )
            )
        else:
            for p in self.deleted_projects:
                deleted_date = (
                    p["deleted_at"][:10] if p["deleted_at"] else "Unknown"
                )
                safe_id = self.sanitize_id(p["trash_folder_name"])
                items_widgets.append(
                    Container(
                        Label(
                            f"Project: {p['project_name']}\n"
                            f"Deleted: {deleted_date} | Remaining: {p['remaining_days']} days",
                            id=f"recycle_bin_label_{safe_id}",
                        ),
                        Horizontal(
                            Button(
                                "Restore",
                                id=f"restore_proj_{safe_id}",
                            ),
                            Button(
                                "Permanently Delete",
                                id=f"perm_del_proj_{safe_id}",
                            ),
                            id=f"recycle_bin_row_buttons_{safe_id}",
                        ),
                        id=f"recycle_bin_card_{safe_id}",
                        classes="recycle_bin_item_card",
                    )
                )

        bottom_buttons = [
            Button("Main Menu", id="recycle_bin_bottom_main_menu_button")
        ]
        if self.deleted_projects:
            bottom_buttons.insert(
                0,
                Button(
                    "Empty Recycle Bin",
                    id="recycle_bin_empty_all_button",
                ),
            )

        yield Container(
            Label("Recycle Bin", id="recycle_bin_banner_label"),
            Vertical(*items_widgets, id="recycle_bin_items_vertical"),
            Horizontal(*bottom_buttons, id="recycle_bin_bottom_horizontal"),
            id="recycle_bin_top_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press on RecycleBinScreen."""
        btn_id = event.button.id or ""

        if btn_id in [
            "all_main_menu_buttons",
            "recycle_bin_bottom_main_menu_button",
        ]:
            self.dismiss()

        elif btn_id == "recycle_bin_empty_all_button":
            self.mainwindow.push_screen(
                modal_dialogs.AcceptOrDeclineMessageBox(
                    self.mainwindow,
                    "Are you sure you want to permanently delete all projects in the Recycle Bin?\n\n"
                    "This action cannot be undone.",
                    accept_button_label="Empty All",
                    decline_button_label="Cancel",
                ),
                self.handle_empty_trash_response,
            )

        elif btn_id.startswith("restore_proj_"):
            safe_id = btn_id[len("restore_proj_") :]
            project = self.find_project_by_safe_id(safe_id)
            if project:
                self.restore_single_project(project["project_name"])

        elif btn_id.startswith("perm_del_proj_"):
            safe_id = btn_id[len("perm_del_proj_") :]
            project = self.find_project_by_safe_id(safe_id)
            if project:
                self.mainwindow.push_screen(
                    modal_dialogs.ConfirmPermanentDeleteModal(
                        self.mainwindow,
                        project_name=project["project_name"],
                    ),
                    lambda result: self.handle_permanent_delete_response(
                        result, project
                    ),
                )

    def restore_single_project(self, project_name: str) -> None:
        """Restore a project and refresh screen."""
        try:
            restore_project_from_trash(project_name)
            self.mainwindow.push_screen(
                modal_dialogs.MessageBox(
                    f"Project '{project_name}' was successfully restored to active projects.",
                    border_color="green",
                ),
                lambda _: self.reload_screen(),
            )
        except Exception as e:
            self.mainwindow.show_modal_error_dialog(str(e))

    def handle_permanent_delete_response(
        self, result: tuple | bool, project: Dict
    ) -> None:
        """Handle response from permanent delete confirmation."""
        if not result:
            return

        project_name = project["project_name"]
        project_path = project["path"]
        try:
            _permanent_delete_project_files(project_name, project_path)
            self.mainwindow.push_screen(
                modal_dialogs.MessageBox(
                    f"Project '{project_name}' was permanently deleted.",
                    border_color="green",
                ),
                lambda _: self.reload_screen(),
            )
        except Exception as e:
            self.mainwindow.show_modal_error_dialog(str(e))

    def handle_empty_trash_response(self, confirmed: bool) -> None:
        """Handle response from empty trash confirmation."""
        if not confirmed:
            return

        try:
            empty_trash()
            self.mainwindow.push_screen(
                modal_dialogs.MessageBox(
                    "The Recycle Bin has been emptied.",
                    border_color="green",
                ),
                lambda _: self.reload_screen(),
            )
        except Exception as e:
            self.mainwindow.show_modal_error_dialog(str(e))

    def reload_screen(self) -> None:
        """Reload the recycle bin screen to update items."""
        self.app.pop_screen()
        self.app.push_screen(RecycleBinScreen(self.mainwindow))

    def find_project_by_safe_id(self, safe_id: str) -> Dict | None:
        """Find deleted project dictionary by sanitized ID."""
        for p in self.deleted_projects:
            if self.sanitize_id(p["trash_folder_name"]) == safe_id:
                return p
        return None

    @staticmethod
    def sanitize_id(name: str) -> str:
        """Convert a folder name to a valid Textual ID."""
        return name.replace(".", "_").replace("-", "_").replace(" ", "_")
