import pytest
from tui_base import TuiBase

from datashuttle.tui.app import TuiApp


class TestTuiSettings(TuiBase):
    """
    Test that the 'Get Help' page from the main menu.
    Open it, check the expected label is displayed, close it.
    """

    @pytest.mark.asyncio
    async def test_light_dark_mode(self, empty_project_paths):

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_get_help_button"
            )

            assert (
                "For help getting started, check out the Documentation"
                in pilot.app.screen.query_one(
                    "#get_help_label"
                ).renderable._text[0]
            )

            await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")

            assert pilot.app.screen.id == "_default"

            await pilot.pause()
