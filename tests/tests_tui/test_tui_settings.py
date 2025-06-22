import pytest

from datashuttle.tui.app import TuiApp

from .tui_base import TuiBase


class TestTuiSettings(TuiBase):
    """Test the 'Settings' screen accessible from the Main Menu."""

    @pytest.mark.asyncio
    async def test_light_dark_mode(self):
        """Check the light / dark mode switch which is stored
        in the global tui settings. Global refers to set
        across all projects not related to a specific project.
        """
        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.scroll_to_click_pause(
                pilot, "#mainwindow_settings_button"
            )

            # Check default is dark mode, switch to light mode
            assert pilot.app.theme == "textual-dark"
            assert pilot.app.load_global_settings()["dark_mode"] is True

            await self.scroll_to_click_pause(
                pilot, "#settings_screen_light_mode_radiobutton"
            )
            assert pilot.app.theme == "textual-light"
            assert pilot.app.load_global_settings()["dark_mode"] is False

            # Switch back to dark mode
            await self.scroll_to_click_pause(
                pilot, "#settings_screen_dark_mode_radiobutton"
            )

            assert pilot.app.theme == "textual-dark"
            assert pilot.app.load_global_settings()["dark_mode"] is True

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_show_transfer_tree_status(self, setup_project_paths):
        """Check the 'show transfer tree' option that turns off transfer
        tree styling by default has the intended effects. It is
        difficult to test whether the tree is actually styled, so
        here all underlying configs + the transfer tree legend
        display is checked.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # First check the show transfer tree styling is off
            # in the project manager tab and legend does not exist.
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "transfer")

            transfer_tab = pilot.app.screen.query_one(
                "#tabscreen_transfer_tab"
            )

            assert transfer_tab.show_legend is False
            assert (
                pilot.app.load_global_settings()["show_transfer_tree_status"]
                is False
            )

            with pytest.raises(BaseException) as e:
                transfer_tab.query_one("#transfer_legend")

            assert "No nodes match" in str(e)
            await pilot.pause()

            # Go to the settings page and turn on transfer tree styling.
            await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_settings_button"
            )

            await self.scroll_to_click_pause(
                pilot, "#show_transfer_tree_status_checkbox"
            )

            await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")

            # Go back to the project manager screen and now
            # check everything is switched on.
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "transfer")

            transfer_tab = pilot.app.screen.query_one(
                "#tabscreen_transfer_tab"
            )
            assert transfer_tab.show_legend is True
            assert (
                pilot.app.load_global_settings()["show_transfer_tree_status"]
                is True
            )
            assert transfer_tab.query_one("#transfer_legend").visible is True

            await pilot.pause()
