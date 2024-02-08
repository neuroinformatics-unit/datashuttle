import re
from pathlib import Path

import pyperclip
import pytest
import test_utils

# https://stackoverflow.com/questions/55893235/pytest-skips-test-saying-asyncio-not
# -installed add to configs
# TODO: do we need to show anything when create folders is clicked?
# TODO: carefully check configs tests after refactor!
# TODO: need to allow name templates to be sub oR ses
# TODO: add green to light mode css
# TODO: could do CTRL+D to input to delete all content .
# test mainmenu button
# test with ssh
# test without ssh
# test bad ssh
# test some configs errors
# TODO: ssh setup not tested, need images!
# test all create files at once
# test all keyboard shortcuts
# test template validation settings etc.
# Settings
# Light / Dark mode
# DirectoryTree Setting
# TODO: don't bother testing tree highlgihting yet.
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
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).tooltip
                == "A sub already exists with the same sub id as sub-001_date-20240208. The existing folder is sub-001."
            )  # TODO: set these inputs to variables

    @pytest.mark.asyncio
    async def test_get_next_sub_and_ses_no_template(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=True
            )

            await self.double_click(pilot, "#create_folders_subject_input")
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-"
            )  # TODO: own get_value function

            await self.double_click(pilot, "#create_folders_session_input")
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-"
            )  # TODO: own get_value function

            await self.double_click(
                pilot, "#create_folders_subject_input", control=True
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_subject_input"
                ).value
                == "sub-002"
            )  # TODO: own get_value function

            await self.fill_input(
                pilot, "#create_folders_subject_input", "sub-001"
            )
            await self.double_click(
                pilot, "#create_folders_session_input", control=True
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_session_input"
                ).value
                == "ses-002"
            )  # TODO: own get_value function

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

    @pytest.mark.asyncio
    async def test_create_folders_directorytree_open_filesystem(
        self, setup_project_paths, monkeypatch
    ):  # TODO: these tests are getting a lot of boilerplate!! stupid await...
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:
            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=True
            )

            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 4
            )  # TODO: maybe add this line to the above function...

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
                press_string="ctrl+o",  # TODO: this line is literally the only thing thats changed compaerd to above...
            )
            assert (
                signal[0]
                == pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(3)
                .data.path.as_posix()
            )

    # TOOD: check all settings widgets... check they change underlying persistent settings. Figure out how to tis thi sin with the rest of persistent settings tests
    # TODO: fully split out all 'widgets' tests.
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

            # TODO: all widget checks moved, just stick to
            # actual create folders tests!
            assert isinstance(
                pilot.app.screen, CreateFoldersSettingsScreen
            )  # TODO: MOVE

            assert (
                pilot.app.screen.interface.tui_settings[
                    "top_level_folder_select"
                ]["create_tab"]
                == "rawdata"
            )  # TODO: MOVE, also check the saved file! critical!
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
            )  # TODO: MOVE, also check the saved file! critical!
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
                project,
                base_folder=(project.cfg["local_path"] / "derivatives"),
                subs=["sub-001"],
                sessions=[
                    "ses-001"
                ],  # TODO: these are defaults linked to `setup_existing_project_create_tab_filled_sub_and_ses`
                folder_used=test_utils.get_all_folders_used(),
            )

    # TODO: TEST EVERYTHING ELSE IN WIDGETS CHECKS. SHOULD PROBABLY DO THAT NOW...

    # maybe separte checks as part of persistent settings to check if they dont change eachother.

    async def test_create_folder_settings_bypass_validation(
        self,
    ):  # check validation errors here also, PROBABLY JUST COMBINE WITH BELOW...
        pass

    async def test_create_folders_settings_name_templates(self):
        pass

    async def test_create_folder_persistent_settings(self):
        pass

    async def get_next_sub_and_ses_with_templates(self):
        pass

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

    @pytest.mark.asyncio
    async def test_create_folders_formatted_names(self, setup_project_paths):
        # TODO: tidy this up, some horrible decisions!
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
                "#create_folders_create_folders_button",  # TODO: just take the key here!!
            )

            project = pilot.app.screen.interface.project
            sub_level_names = list(
                (project.cfg["local_path"] / "rawdata").glob("sub-*")
            )

            assert re.fullmatch(sub_1_regexp, sub_level_names[0].stem)
            assert re.fullmatch(sub_2_regexp, sub_level_names[1].stem)

            for sub in sub_level_names:
                ses_level_names = list(
                    (project.cfg["local_path"] / "rawdata" / sub).glob("ses-*")
                )

                assert re.fullmatch(ses_1_regexp, ses_level_names[0].stem)
                assert re.fullmatch(ses_2_regexp, ses_level_names[1].stem)
                assert re.fullmatch(ses_3_regexp, ses_level_names[2].stem)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def turn_off_all_datatype_checkboxes(self, pilot):
        """
        Make sure all checkboxes are off to start
        """
        for datatype in canonical_folders.get_datatype_folders().keys():
            id = f"#create_{datatype}_checkbox"
            if pilot.app.screen.query_one(id).value:
                await self.scroll_to_click_pause(pilot, id)
                # I don't know why the click is not triggered this, but it
                # does outside the test environment. sBut this is super critical
                # It is necessary this function is called on click to update .datatype_config.
                pilot.app.screen.query_one(
                    "#create_folders_datatype_checkboxes"
                ).on_checkbox_changed()
                await pilot.pause()

        datatype_config = pilot.app.screen.query_one(
            "#create_folders_datatype_checkboxes"
        ).datatype_config
        assert all(val is False for val in datatype_config.values())

    async def create_folders_and_check_output(
        self, pilot, project, subs, sessions, folder_used
    ):
        """"""
        await self.scroll_to_click_pause(
            pilot,
            "#create_folders_create_folders_button",
        )

        test_utils.check_folder_tree_is_correct(
            project,
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

    async def click_create_folders_and_check_messagebox(
        self, pilot
    ):  # USE FOR ERROR

        await self.scroll_to_click_pause(
            pilot,
            "#create_folders_create_folders_button",
        )

        assert isinstance(pilot.app.screen, MessageBox)
        assert pilot.app.screen.query_one(
            "#messagebox_message_label"
        ).renderable._text[0]
