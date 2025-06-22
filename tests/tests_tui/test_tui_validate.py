import warnings

import pytest
import textual

import datashuttle
from datashuttle.tui.app import TuiApp

from .tui_base import TuiBase


class TestTuiValidate(TuiBase):
    @pytest.mark.asyncio
    async def test_validate_on_project_manager_output(
        self, setup_project_paths
    ):
        """Check that the validate RichLog is updated as expected."""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Go to the validate tab on project manager, make
            # some badly formatted files.
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

            # Validate and check validation results are
            # shown on the Richlog.
            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )

            written_lines = [
                ele.text
                for ele in pilot.app.screen.query_one(
                    "#validate_richlog"
                ).lines
            ]

            assert len(written_lines) == 3
            assert "BAD_VALUE:" in written_lines[0]

    @pytest.mark.asyncio
    async def test_validate_on_project_manager_kwargs(
        self, setup_project_paths, mocker
    ):
        """Check options are properly passed through to validate_project
        from the project manager validate tab (using mocker).
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Set up a project and open the validate tab
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "validate")

            # First, check that the default arguments are passed
            # through to `DataShuttle.validate_project` as expected.
            spy_validate = mocker.spy(
                datashuttle.utils.validation, "validate_project"
            )

            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )

            args_, kwargs_ = spy_validate.call_args_list[0]

            assert "local_path" in args_[0]
            assert args_[1] == ["rawdata"]
            assert kwargs_["include_central"] is False
            assert kwargs_["display_mode"] == "print"
            assert kwargs_["name_templates"] == {
                "on": False,
                "sub": None,
                "ses": None,
            }
            assert kwargs_["strict_mode"] is False

            # Then, change all arguments and check these are
            # changed at the level of the called function.

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

            assert (
                "`strict_mode` is currently only available"
                in pilot.app.screen.message
            )

            await self.close_messagebox(pilot)

            await self.change_checkbox(pilot, "#validate_strict_mode_checkbox")

            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )

            args_, kwargs_ = spy_validate.call_args_list[1]

            assert "local_path" in args_[0]
            assert args_[1] == ["rawdata", "derivatives"]
            assert kwargs_["include_central"] is True
            assert kwargs_["display_mode"] == "print"
            assert kwargs_["name_templates"] == {
                "on": False,
                "sub": None,
                "ses": None,
            }
            assert kwargs_["strict_mode"] is False

            # Check the widgets are hidden as expected.
            # Path widgets are not shown for Transfer tab
            for id in [
                "validate_path_label",
                "validate_path_input",
                "validate_select_button",
                "validate_path_container",
            ]:
                with pytest.raises(textual.css.query.InvalidQueryFormat):
                    pilot.app.screen.query_one(id)

    @pytest.mark.asyncio
    async def test_validate_at_path_kwargs(self, setup_project_paths, mocker):
        """Test kwargs are properly passed through from the TUI to `quick_validate_project`
        with mocker. Note that the 'Select' button / directorytree is not tested here,
        as the screen is tested elsewhere and it's non-critical feature here.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Open the validation window and input path to project
            project_path = (tmp_path / "local" / project_name).as_posix()

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_validate_from_project_path"
            )
            await self.fill_input(pilot, "#validate_path_input", project_path)

            # Spy the function and click 'validate' button
            spy_validate = mocker.spy(
                datashuttle.tui.shared.validate_content,
                "quick_validate_project",
            )

            warnings.filterwarnings("ignore")
            await self.scroll_to_click_pause(
                pilot, "#validate_validate_button"
            )
            warnings.filterwarnings("default")

            # Check args are passed through to function as expected
            args_, kwargs_ = spy_validate.call_args_list[0]

            assert args_[0] == project_path
            assert kwargs_["top_level_folder"] == "rawdata"
            assert kwargs_["strict_mode"] is False

            # Check removed widgets, this should be removed because always local
            with pytest.raises(textual.css.query.InvalidQueryFormat):
                pilot.app.screen.query_one("validate_include_central_checkbox")
