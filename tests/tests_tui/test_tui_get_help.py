import pytest
from tui_base import TuiBase

from datashuttle.tui.app import TuiApp


class TestTuiSettings(TuiBase):

    @pytest.mark.asyncio
    async def test_light_dark_mode(self, empty_project_paths):

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_get_help_button"
            )

            assert (
                "For help getting started, check out the Documentation"
                in pilot.app.screen.query_one(
                    "#get_help_label"
                ).renderable._text[0]
            )

            await self.scroll_to_click_pause(
                pilot, "#generic_screen_close_button"
            )

            assert pilot.app.screen.id == "_default"

            await pilot.pause()
