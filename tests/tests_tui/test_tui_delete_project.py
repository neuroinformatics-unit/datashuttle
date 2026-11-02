import pytest
from textual.widgets import Button

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import (
    ConfirmDeleteProjectModal,
    MessageBox,
)
from datashuttle.tui.screens.project_manager import ProjectManagerScreen

from .tui_base import TuiBase


class TestTuiDeleteProject(TuiBase):
    @pytest.mark.asyncio
    async def test_tui_delete_project_cancel(self, setup_project_paths):
        """Test clicking 'Delete Project' and then cancelling the modal dialog."""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()
        project_config_dir = tmp_config_path / project_name

        assert project_config_dir.is_dir()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "configs")

            delete_button = pilot.app.screen.query_one(
                "#configs_delete_project_button"
            )
            assert delete_button.visible is True

            await pilot.click("#configs_delete_project_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmDeleteProjectModal)

            await pilot.click("#confirm_delete_project_cancel_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ProjectManagerScreen)
            assert project_config_dir.is_dir()

    @pytest.mark.asyncio
    async def test_tui_delete_project_soft_delete(self, setup_project_paths):
        """Test clicking 'Delete Project' and choosing Move to Trash."""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()
        project_config_dir = tmp_config_path / project_name

        assert project_config_dir.is_dir()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "configs")

            await pilot.click("#configs_delete_project_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmDeleteProjectModal)

            await pilot.click("#confirm_delete_project_trash_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, MessageBox)
            assert "Recycle Bin" in pilot.app.screen.message

            # Click OK on the success message box
            await pilot.click("#messagebox_ok_button Button")
            await pilot.pause()

            assert not project_config_dir.exists()

    @pytest.mark.asyncio
    async def test_tui_delete_project_permanent_wrong_name_blocked(
        self, setup_project_paths
    ):
        """Test typing wrong name for permanent delete is blocked by error dialog."""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()
        project_config_dir = tmp_config_path / project_name

        assert project_config_dir.is_dir()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "configs")

            await pilot.click("#configs_delete_project_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmDeleteProjectModal)

            # Type wrong project name
            await self.fill_input(
                pilot, "#confirm_delete_project_name_input", "wrong_name"
            )

            await pilot.click("#confirm_delete_project_permanent_button")
            await pilot.pause()

            # Error dialog is shown
            assert isinstance(pilot.app.screen, MessageBox)
            assert (
                "Project name confirmation failed" in pilot.app.screen.message
            )

            await pilot.click("#messagebox_ok_button Button")
            await pilot.pause()

            # Modal is still open and project is NOT deleted
            assert isinstance(pilot.app.screen, ConfirmDeleteProjectModal)
            assert project_config_dir.is_dir()

    @pytest.mark.asyncio
    async def test_tui_delete_project_permanent_matching_name(
        self, setup_project_paths
    ):
        """Test typing matching project name permanently deletes the project."""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()
        project_config_dir = tmp_config_path / project_name

        assert project_config_dir.is_dir()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "configs")

            await pilot.click("#configs_delete_project_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmDeleteProjectModal)

            # Type exact matching project name
            await self.fill_input(
                pilot, "#confirm_delete_project_name_input", project_name
            )

            await pilot.click("#confirm_delete_project_permanent_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, MessageBox)
            assert "permanently deleted" in pilot.app.screen.message

            await pilot.click("#messagebox_ok_button Button")
            await pilot.pause()

            assert not project_config_dir.exists()

    @pytest.mark.asyncio
    async def test_tui_recycle_bin_screen_restore(self, setup_project_paths):
        """Test viewing Recycle Bin from Main Menu and restoring a project."""
        from datashuttle import delete_project_from_disk
        from datashuttle.tui.screens.recycle_bin import RecycleBinScreen

        tmp_config_path, tmp_path, project_name = setup_project_paths.values()
        project_config_dir = tmp_config_path / project_name

        # Soft delete the project into trash
        delete_project_from_disk(
            project_name, soft_delete=True, retention_days=30
        )
        assert not project_config_dir.exists()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Click Recycle Bin button on Main Menu
            await pilot.click("#mainwindow_recycle_bin_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, RecycleBinScreen)

            # Click Restore button on the project item
            restore_btns = [
                b
                for b in pilot.app.screen.query(Button)
                if b.id and b.id.startswith("restore_proj_")
            ]
            assert len(restore_btns) >= 1
            await pilot.click(f"#{restore_btns[0].id}")
            await pilot.pause()

            # Dismiss success dialog
            assert isinstance(pilot.app.screen, MessageBox)
            await pilot.click("#messagebox_ok_button Button")
            await pilot.pause()

            # Verify the project directory is restored
            assert project_config_dir.is_dir()
            assert (project_config_dir / "config.yaml").is_file()

    @pytest.mark.asyncio
    async def test_tui_recycle_bin_screen_permanent_delete(
        self, setup_project_paths
    ):
        """Test permanently deleting a single project from inside the Recycle Bin."""
        from datashuttle import delete_project_from_disk, get_deleted_projects
        from datashuttle.tui.screens.modal_dialogs import (
            ConfirmPermanentDeleteModal,
        )
        from datashuttle.tui.screens.recycle_bin import RecycleBinScreen

        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        # Soft delete project
        delete_project_from_disk(
            project_name, soft_delete=True, retention_days=30
        )
        assert len(get_deleted_projects()) >= 1

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await pilot.click("#mainwindow_recycle_bin_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, RecycleBinScreen)

            # Click Permanently Delete button on the project item
            perm_del_btns = [
                b
                for b in pilot.app.screen.query(Button)
                if b.id and b.id.startswith("perm_del_proj_")
            ]
            assert len(perm_del_btns) >= 1
            await pilot.click(f"#{perm_del_btns[0].id}")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmPermanentDeleteModal)

            # Type exact matching project name
            await self.fill_input(
                pilot, "#confirm_permanent_delete_name_input", project_name
            )

            await pilot.click("#confirm_permanent_delete_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, MessageBox)
            assert "permanently deleted" in pilot.app.screen.message

            await pilot.click("#messagebox_ok_button Button")
            await pilot.pause()

            assert len(get_deleted_projects()) == 0

    @pytest.mark.asyncio
    async def test_tui_recycle_bin_empty_all(self, setup_project_paths):
        """Test emptying the entire Recycle Bin from RecycleBinScreen."""
        from datashuttle import delete_project_from_disk, get_deleted_projects
        from datashuttle.tui.screens.modal_dialogs import (
            AcceptOrDeclineMessageBox,
        )
        from datashuttle.tui.screens.recycle_bin import RecycleBinScreen

        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        # Soft delete project
        delete_project_from_disk(
            project_name, soft_delete=True, retention_days=30
        )
        assert len(get_deleted_projects()) >= 1

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await pilot.click("#mainwindow_recycle_bin_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, RecycleBinScreen)

            await pilot.click("#recycle_bin_empty_all_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, AcceptOrDeclineMessageBox)

            await pilot.click("#accept_or_decline_messagebox_accept_button")
            await pilot.pause()

            assert isinstance(pilot.app.screen, MessageBox)
            await pilot.click("#messagebox_ok_button Button")
            await pilot.pause()

            assert len(get_deleted_projects()) == 0
