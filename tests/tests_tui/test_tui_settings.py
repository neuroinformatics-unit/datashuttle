import pytest
from tui_base import TuiBase

from datashuttle.tui.app import TuiApp


class TestTuiSettings(TuiBase):

    @pytest.mark.asyncio
    async def test_light_dark_mode(self, empty_project_paths):

        tmp_config_path, tmp_path, project_name = empty_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_settings_button"
            )

            assert pilot.app.dark is True
            assert pilot.app.load_global_settings()["dark_mode"] is True

            await self.scroll_to_click_pause(
                pilot, "#settings_screen_light_mode_radiobutton"
            )

            assert pilot.app.dark is False
            assert pilot.app.load_global_settings()["dark_mode"] is False

            await self.scroll_to_click_pause(
                pilot, "#settings_screen_dark_mode_radiobutton"
            )

            assert pilot.app.dark is True
            assert pilot.app.load_global_settings()["dark_mode"] is True

    @pytest.mark.asyncio
    async def test_show_transfer_tree_status(self, setup_project_paths):
        # doesn't actually test coloring. non-critical
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

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

            assert "No nodes match <DOMQuery query" in str(e)
            await pilot.pause()

            await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_settings_button"
            )

            await self.scroll_to_click_pause(
                pilot, "#show_transfer_tree_status_checkbox"
            )

            await self.scroll_to_click_pause(
                pilot, "#generic_screen_close_button"
            )

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
