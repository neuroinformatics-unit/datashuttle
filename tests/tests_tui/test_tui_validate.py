import pytest
import textual
from tui_base import TuiBase

from datashuttle.tui.app import TuiApp


class TestTuiValidate(TuiBase):

    @pytest.mark.asyncio
    async def test_validate_on_project_manager_output(
        self, setup_project_paths
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "validate")

            project = pilot.app.screen.interface.project

            (
                project.get_local_path()
                / "rawdata"
                / "sub-01x"
                / "ses-00x"
                / "ephys"
            ).mkdir(parents=True, exist_ok=True)
            (
                project.get_local_path()
                / "rawdata"
                / "sub-002"
                / "ses-001"
                / "bad_dtype"
            ).mkdir(parents=True, exist_ok=True)
            (
                project.get_local_path()
                / "rawdata"
                / "sub-002"
                / "ses-badname"
            ).mkdir(parents=True, exist_ok=True)

            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )
            written_lines = [
                ele.text
                for ele in pilot.app.query_one("#validate_richlog").lines
            ]

            assert len(written_lines) == 4
            assert "TOP_LEVEL_FOLDER:" in written_lines[0]

    @pytest.mark.asyncio
    async def test_validate_on_project_manager_kwargs(
        self, setup_project_paths, mocker
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "validate")

            import datashuttle

            spy_validate = mocker.spy(
                datashuttle.utils.validation, "validate_project"
            )

            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )

            args_, kwargs_ = spy_validate.call_args_list[0]

            assert "local_path" in args_[0]
            assert args_[1] == ["rawdata"]
            assert kwargs_["local_only"] is False
            assert kwargs_["display_mode"] == "print"
            assert kwargs_["name_templates"] == {
                "on": False,
                "sub": None,
                "ses": None,
            }
            assert kwargs_["strict_mode"] is False

            await self.move_select_to_position(
                pilot, "#validate_top_level_folder_select", position=6
            )  # switch to both
            await self.change_checkbox(
                pilot, "#validate_include_central_checkbox"
            )
            await self.change_checkbox(pilot, "#validate_strict_mode_checkbox")

            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )

            args_, kwargs_ = spy_validate.call_args_list[1]

            assert "local_path" in args_[0]
            assert args_[1] == ["rawdata", "derivatives"]
            assert kwargs_["local_only"] is True
            assert kwargs_["display_mode"] == "print"
            assert kwargs_["name_templates"] == {
                "on": False,
                "sub": None,
                "ses": None,
            }
            assert kwargs_["strict_mode"] is True

            # TODO: AFTER REBASE INCLUDE AND CHECK STRICT MODE
            # TODO: tooltips

            # Path widgets are not shown for Transfer tab
            for id in [
                "validate_path_label",
                "validate_path_input",
                "validate_select_button",
                "validate_path_container",
            ]:
                with pytest.raises(textual.css.query.InvalidQueryFormat):
                    pilot.app.query_one(id)

    @pytest.mark.asyncio
    async def test_validate_at_path_kwargs(self, setup_project_paths, mocker):
        """ """
        # select is not tested, its not criticla and the widget is tested elsewhere.
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:

            project_path = (tmp_path / "local" / project_name).as_posix()

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_validate_from_project_path"
            )
            await self.fill_input(pilot, "#validate_path_input", project_path)

            import datashuttle

            spy_validate = mocker.spy(
                datashuttle.tui.screens.validate, "quick_validate_project"
            )

            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )

            args_, kwargs_ = spy_validate.call_args_list[0]

            assert args_[0] == project_path
            assert kwargs_["top_level_folder"] == "rawdata"
            assert kwargs_["strict_mode"] is False

            with pytest.raises(textual.css.query.InvalidQueryFormat):
                # should be removed because always local
                pilot.app.query_one("validate_include_central_checkbox")
