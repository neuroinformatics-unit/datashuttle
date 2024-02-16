import re
from pathlib import Path

import pyperclip
import pytest
import test_utils
from tui_base import TuiBase

from datashuttle.configs import canonical_folders
from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.create_folder_settings import (
    CreateFoldersSettingsScreen,
)
from datashuttle.tui.screens.modal_dialogs import (
    MessageBox,
)
from datashuttle.tui.screens.project_manager import ProjectManagerScreen

try:
    pyperclip.paste()
    HAS_GUI = True
except pyperclip.PyperclipException:
    HAS_GUI = False


class TestTuiCreateFolders(TuiBase):
    @pytest.mark.asyncio
    async def test_create_folders_bad_validation_tooltips(
        self, setup_project_paths
    ):
        # Not exhaustive
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            # SUB
            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-abc"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).tooltip
                == "Invalid character in subject or session value: abc"
            )

            # SES
            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-001_ses-001"
            )

            # Unfortunately the validation is currently setup to validate both subject and
            # session together
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).tooltip
                == "Invalid character in subject or session value: abc"
            )

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001"
            )

            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).tooltip
                == "Formatted names: ['sub-001']"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).tooltip
                == "There is more than one instance of ses in ses-001_ses-001. NeuroBlueprint names must contain only one instance of each key."
            )

            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-001"
            )

            await self.scroll_to_click_pause(
                pilot,
                "#create_folders_create_folders_button",
            )

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001_@DATE@"
            )
            assert (
                "A sub already exists with the same sub id as"
                in pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).tooltip
            )

            await pilot.pause()

    # This comes under some kind of 'settings' tab
    @pytest.mark.asyncio
    async def test_validation_error_and_bypass_validation(
        self, setup_project_paths
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-abc"
            )
            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-abc"
            )

            await self.scroll_to_click_pause(
                pilot, "#create_folders_create_folders_button"
            )

            assert (
                pilot.app.screen.query_one(
                    "#messagebox_message_label"
                ).renderable._text[0]
                == "Invalid character in subject or session value: abc"
            )
            await self.close_messagebox(pilot)
            assert not any(
                list(
                    (
                        pilot.app.screen.interface.project.cfg["local_path"]
                        / "rawdata"
                    ).glob("*")
                )
            )
            await self.scroll_to_click_pause(
                pilot, "#create_folders_settings_button"
            )
            await self.scroll_to_click_pause(
                pilot, "#create_folders_settings_bypass_validation_checkbox"
            )
            await self.scroll_to_click_pause(
                pilot, "#create_folders_settings_close_button"
            )

            await self.scroll_to_click_pause(
                pilot, "#create_folders_create_folders_button"
            )
            assert (
                pilot.app.screen.interface.project.cfg["local_path"]
                / "rawdata"
                / "sub-abc"
            ).is_dir()
            assert (
                pilot.app.screen.interface.project.cfg["local_path"]
                / "rawdata"
                / "sub-abc"
                / "ses-abc"
            ).is_dir()

            await pilot.pause()

    # Check name templates with get next sub and ses here!

    @pytest.mark.asyncio
    async def test_name_template_next_sub_or_ses_and_validation(
        self, setup_project_paths
    ):
        """ """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            # Set some name template and check the tooltips indicate mismatches correctly
            pilot.app.screen.interface.project.set_name_templates(
                {"on": True, "sub": "sub-\d\d\d", "ses": "ses-...."}
            )

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-0001"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).tooltip
                == "The name: sub-0001 does not match the template: sub-\\d\\d\\d"
            )

            # It is expected that sub errors propagate to session input. This is because
            # subject and ses must be validated at the same time, to check duplicate ses
            # within subjects.
            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-0001"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).tooltip
                == "The name: sub-0001 does not match the template: sub-\\d\\d\\d"
            )

            # Try and make the folders, displaying a validation error.
            await self.scroll_to_click_pause(
                pilot, "#create_folders_create_folders_button"
            )

            pilot.app.screen.query_one(
                "#messagebox_message_label"
            ).renderable._text[
                0
            ] = "The name: sub-0001 does not match the template: sub-\\d\\d\\d"
            await self.close_messagebox(pilot)

            # Now make the correct folders respecting the name templates
            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001"
            )

            await self.scroll_to_click_pause(
                pilot, "#create_folders_create_folders_button"
            )

            # Now fill in a bad ses name template, because we tested sub above but not ses.
            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-001"
            )

            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).tooltip
                == "Formatted names: ['sub-001']"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).tooltip
                == "The name: ses-001 does not match the template: ses-...."
            )

            # Finally, double click the input to suggest next ses / sub numbers, which should
            # respect the name templates.
            await self.double_click(
                pilot, "#create_folders_subject_input", control=True
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-\\d\\d\\d"
            )

            await self.double_click(
                pilot, "#create_folders_session_input", control=True
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-...."
            )

            await self.double_click(
                pilot, "#create_folders_subject_input", control=False
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-002"
            )

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001"
            )
            await self.double_click(
                pilot, "#create_folders_session_input", control=False
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-0002"
            )
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_get_next_sub_and_ses_no_template(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=True
            )

            await self.double_click(
                pilot, "#create_folders_subject_input", control=True
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-"
            )  # TODO: own get_value function

            await self.double_click(
                pilot, "#create_folders_session_input", control=True
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-"
            )  # TODO: own get_value function

            await self.double_click(pilot, "#create_folders_subject_input")
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-002"
            )  # TODO: own get_value function

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001"
            )
            await self.double_click(pilot, "#create_folders_session_input")
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-002"
            )  # TODO: own get_value function

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_fill_and_append_next_sub_and_ses(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001"
            )
            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-001"
            )
            await self.scroll_to_click_pause(
                pilot,
                "#create_folders_create_folders_button",
            )

            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 4
            )

            await self.hover_and_press_tree(
                pilot,
                "#create_folders_directorytree",
                hover_line=2,
                press_string="ctrl+a",
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-001, sub-001"
            )

            await self.hover_and_press_tree(
                pilot,
                "#create_folders_directorytree",
                hover_line=3,
                press_string="ctrl+a",
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-001, ses-001"
            )

            await self.hover_and_press_tree(
                pilot,
                "#create_folders_directorytree",
                hover_line=2,
                press_string="ctrl+f",
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-001"
            )

            await self.hover_and_press_tree(
                pilot,
                "#create_folders_directorytree",
                hover_line=3,
                press_string="ctrl+f",
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-001"
            )

            await pilot.pause()

    @pytest.mark.skipif(HAS_GUI is False, reason="Requires system has GUI.")
    @pytest.mark.asyncio
    async def test_create_folders_directorytree_clipboard(
        self, setup_project_paths
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:
            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=True
            )

            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 4
            )
            await self.hover_and_press_tree(
                pilot,
                "#create_folders_directorytree",
                hover_line=2,
                press_string="ctrl+q",
            )

            pasted_path = pyperclip.paste()

            assert (
                pasted_path
                == pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(2)
                .data.path.as_posix()
            )

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_create_folders_directorytree_open_filesystem(
        self, setup_project_paths, monkeypatch
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:
            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=True
            )

            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 4
            )

            signal = [Path()]

            def set_signal_to_path(path_):
                signal[0] = path_

            monkeypatch.setattr(
                "showinfm.show_in_file_manager", set_signal_to_path
            )

            assert signal[0] == Path()
            await self.hover_and_press_tree(
                pilot,
                "#create_folders_directorytree",
                hover_line=3,
                press_string="ctrl+o",
            )
            assert (
                signal[0]
                == pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(3)
                .data.path.as_posix()
            )

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_create_folders_settings_top_level_folder(
        self, setup_project_paths
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:
            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=False
            )

            await self.scroll_to_click_pause(
                pilot, "#create_folders_settings_button"
            )

            assert isinstance(pilot.app.screen, CreateFoldersSettingsScreen)

            assert (
                pilot.app.screen.interface.tui_settings[
                    "top_level_folder_select"
                ]["create_tab"]
                == "rawdata"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_settings_toplevel_select"
                ).value
                == "rawdata"
            )

            await pilot.click("#create_folders_settings_toplevel_select")
            await pilot.click(
                "#create_folders_settings_toplevel_select", offset=(2, 5)
            )
            await pilot.pause()

            assert (
                pilot.app.screen.interface.tui_settings[
                    "top_level_folder_select"
                ]["create_tab"]
                == "derivatives"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_settings_toplevel_select"
                ).value
                == "derivatives"
            )

            await self.scroll_to_click_pause(
                pilot, "#create_folders_settings_close_button"
            )

            assert isinstance(pilot.app.screen, ProjectManagerScreen)

            await self.scroll_to_click_pause(
                pilot, "#create_folders_create_folders_button"
            )

            project = pilot.app.screen.interface.project
            test_utils.check_folder_tree_is_correct(
                base_folder=(project.cfg["local_path"] / "derivatives"),
                subs=["sub-001"],
                sessions=["ses-001"],
                folder_used=test_utils.get_all_folders_used(),
            )

            await pilot.pause()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_multi_input", [True, False])
    async def test_create_folders_single_sub_and_ses(
        self, setup_project_paths, test_multi_input
    ):
        """ """
        # We could create test_lists from text but we want to be SUPER explicitly here
        if test_multi_input:
            sub_text = "sub-001, sub-002"
            sub_test_list = ["sub-001", "sub-002"]
            ses_text = "ses-001,ses-010"
            ses_test_list = ["ses-001", "ses-010"]
        else:
            sub_text = "sub-001"
            sub_test_list = [sub_text]
            ses_text = "ses-001"
            ses_test_list = [ses_text]

        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            project = pilot.app.screen.interface.project

            await self.turn_off_all_datatype_checkboxes(pilot)

            await self.fill_input(
                pilot, "#create_folders_subject_input", sub_text
            )

            await self.create_folders_and_check_output(
                pilot,
                project,
                subs=sub_test_list,
                sessions=[],
                folder_used=test_utils.get_all_folders_used(value=False),
            )

            await self.fill_input(
                pilot, "#create_folders_session_input", ses_text
            )
            await self.create_folders_and_check_output(
                pilot,
                project,
                subs=sub_test_list,
                sessions=ses_test_list,
                folder_used=test_utils.get_all_folders_used(value=False),
            )

            await self.iterate_and_check_all_datatype_folders(
                pilot, subs=sub_test_list, sessions=ses_test_list
            )

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_create_folders_formatted_names(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            # SUB
            await self.fill_input(
                pilot,
                "#create_folders_subject_input",
                "sub-001_@DATE@, sub-002_@DATE@",
            )

            sub_1_regexp = "sub\-001_date\-\d{8}"
            sub_2_regexp = "sub\-002_date\-\d{8}"
            sub_tooltip_regexp = (
                "Formatted names: \['"
                + sub_1_regexp
                + "', '"
                + sub_2_regexp
                + "'\]"
            )
            sub_tooltip = pilot.app.screen.query_one(
                "#create_folders_subject_input"
            ).tooltip

            assert re.fullmatch(sub_tooltip_regexp, sub_tooltip)

            # SES
            await self.fill_input(
                pilot, "#create_folders_session_input", "ses-001@TO@003_@DATE@"
            )

            ses_1_regexp = "ses\-001_date\-\d{8}"
            ses_2_regexp = "ses\-002_date\-\d{8}"
            ses_3_regexp = "ses\-003_date\-\d{8}"
            ses_tooltip_regexp = (
                "Formatted names: \['"
                + ses_1_regexp
                + "', '"
                + ses_2_regexp
                + "', '"
                + ses_3_regexp
                + "'\]"
            )
            ses_tooltip = pilot.app.screen.query_one(
                "#create_folders_session_input"
            ).tooltip
            assert re.fullmatch(ses_tooltip_regexp, ses_tooltip)

            await self.scroll_to_click_pause(
                pilot,
                "#create_folders_create_folders_button",
            )

            project = pilot.app.screen.interface.project
            sub_level_names = sorted(
                list((project.cfg["local_path"] / "rawdata").glob("sub-*"))
            )

            assert re.fullmatch(sub_1_regexp, sub_level_names[0].stem)
            assert re.fullmatch(sub_2_regexp, sub_level_names[1].stem)

            for sub in sub_level_names:
                ses_level_names = sorted(
                    list(
                        (project.cfg["local_path"] / "rawdata" / sub).glob(
                            "ses-*"
                        )
                    )
                )

                assert re.fullmatch(ses_1_regexp, ses_level_names[0].stem)
                assert re.fullmatch(ses_2_regexp, ses_level_names[1].stem)
                assert re.fullmatch(ses_3_regexp, ses_level_names[2].stem)

            await pilot.pause()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def create_folders_and_check_output(
        self, pilot, project, subs, sessions, folder_used
    ):
        """"""
        await self.scroll_to_click_pause(
            pilot,
            "#create_folders_create_folders_button",
        )

        test_utils.check_folder_tree_is_correct(
            base_folder=test_utils.get_top_level_folder_path(project),
            subs=subs,
            sessions=sessions,
            folder_used=folder_used,
        )

    async def iterate_and_check_all_datatype_folders(
        self, pilot, subs, sessions
    ):
        """ """
        project = pilot.app.screen.interface.project
        folder_used = test_utils.get_all_folders_used(value=False)

        for datatype in canonical_folders.get_datatype_folders().keys():

            await self.scroll_to_click_pause(
                pilot,
                f"#create_{datatype}_checkbox",
            )
            folder_used[datatype] = True

            await self.create_folders_and_check_output(
                pilot, project, subs, sessions, folder_used
            )

    async def click_create_folders_and_check_messagebox(self, pilot):
        await self.scroll_to_click_pause(
            pilot,
            "#create_folders_create_folders_button",
        )

        assert isinstance(pilot.app.screen, MessageBox)
        assert pilot.app.screen.query_one(
            "#messagebox_message_label"
        ).renderable._text[0]
