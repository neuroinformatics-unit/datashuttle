import copy
import re
from pathlib import Path

import pyperclip
import pytest
import pytest_asyncio
import test_utils
from textual.widgets._tabbed_content import ContentTab

from datashuttle.configs import canonical_folders
from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import (
    MessageBox,
    SelectDirectoryTreeScreen,
)
from datashuttle.tui.screens.new_project import NewProjectScreen
from datashuttle.tui.screens.project_manager import ProjectManagerScreen
from datashuttle.tui.screens.project_selector import ProjectSelectorScreen

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


class TuiBase:
    @pytest_asyncio.fixture(scope="function")
    async def empty_project_paths(self, tmp_path_factory, monkeypatch):
        """
        Get the paths and project name for a non-existent (i.e. not
        yet setup) project.
        """
        project_name = "my-test-project"
        tmp_path = tmp_path_factory.mktemp("test")
        tmp_config_path = tmp_path / "config"

        self.monkeypatch_get_datashuttle_path(tmp_config_path, monkeypatch)
        self.monkeypatch_print(monkeypatch)

        assert not any(list(tmp_config_path.glob("**")))

        yield {
            "tmp_config_path": tmp_config_path,
            "tmp_path": tmp_path,
            "project_name": project_name,
        }

    @pytest_asyncio.fixture(scope="function")
    async def setup_project_paths(self, empty_project_paths):
        """
        Get the paths and project name for a setup project.
        """
        test_utils.setup_project_fixture(
            empty_project_paths["tmp_path"],
            empty_project_paths["project_name"],
        )

        return empty_project_paths

    def monkeypatch_get_datashuttle_path(self, tmp_config_path, _monkeypatch):
        """
        For these tests, store the datashuttle configs (usually stored in
        Path.home()) in the `tmp_path` provided by pytest, as it simplifies
        testing here.

        This is not done for general tests because
        1) It is further from the actual datashuttle behaviour
        2) It fails for testing CLI, because CLI spawns a new process in
           which `get_datashuttle_path()` is not monkeypatched.
        """

        def mock_get_datashuttle_path():
            return tmp_config_path

        _monkeypatch.setattr(
            "datashuttle.configs.canonical_folders.get_datashuttle_path",
            mock_get_datashuttle_path,
        )

    def monkeypatch_print(self, _monkeypatch):
        """
        Calls to `print` in datashuttle crash the TUI in the
        test environment. I am not sure why. Get around this
        in tests by monkeypatching the datashuttle print method.
        """

        def return_none(arg1, arg2=None):
            return

        _monkeypatch.setattr(
            "datashuttle.utils.utils.print_message_to_user", return_none
        )

    async def fill_input(self, pilot, id, value):
        await self.scroll_to_click_pause(pilot, id)
        pilot.app.screen.query_one(id).value = ""
        await pilot.press(*value)
        await pilot.pause()

    async def setup_existing_project_create_tab_filled_sub_and_ses(
        self, pilot, project_name, create_folders=False
    ):
        """"""
        await self.check_and_click_onto_existing_project(pilot, project_name)

        await self.fill_input(
            pilot, "#create_folders_subject_input", "sub-001"
        )
        await self.fill_input(
            pilot, "#create_folders_session_input", "ses-001"
        )
        if create_folders:
            await self.scroll_to_click_pause(
                pilot,
                "#create_folders_create_folders_button",
            )

    async def double_click(self, pilot, id, control=False):
        for _ in range(2):
            await self.scroll_to_click_pause(pilot, id, control=control)

    async def reload_tree_nodes(self, pilot, id, num_nodes):
        """
        Not sure whyt this is necsaey
        """
        for node in range(4):
            await pilot.app.screen.query_one(id).reload_node(
                pilot.app.screen.query_one(id).get_node_at_line(node)
            )

    async def hover_and_press_tree(self, pilot, id, hover_line, press_string):
        pilot.app.screen.query_one(id).hover_line = hover_line
        await self.press_tree(pilot, id, press_string)

    async def press_tree(self, pilot, id, press_string):
        await self.scroll_to_click_pause(pilot, id)
        await pilot.press(press_string)
        await pilot.pause()

    # TODO: for all shared directorytree fujnctions, do on both trees!

    async def scroll_to_and_pause(self, pilot, id):
        """
        Scroll to a widget and pause.
        """
        widget = pilot.app.screen.query_one(id)
        widget.scroll_visible(animate=False)
        await pilot.pause()

    async def scroll_to_click_pause(self, pilot, id, control=False):
        """
        Scroll to a widget, click it and call pause.
        """

        await self.scroll_to_and_pause(pilot, id)
        await pilot.click(id, control=control)
        await pilot.pause()

    async def check_and_click_onto_existing_project(self, pilot, project_name):
        """
        From the main menu, go onto the select project page and
        select the project created in the test environment.
        Perform general TUI checks during the navigation.
        """
        await pilot.click("#mainwindow_existing_project_button")

        assert isinstance(pilot.app.screen, ProjectSelectorScreen)
        assert len(pilot.app.screen.project_names) == 1
        assert project_name in pilot.app.screen.project_names

        await pilot.click(f"#{project_name}")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ProjectManagerScreen)
        assert pilot.app.screen.title == f"Project: {project_name}"
        assert (
            pilot.app.screen.query_one("#tabscreen_tabbed_content").active
            == "tabscreen_create_tab"
        )

    # TODO: check local / central path deleted!

    async def change_checkbox(self, pilot, id):
        pilot.app.screen.query_one(id).toggle()
        await pilot.pause()

    async def turn_off_all_datatype_checkboxes(self, pilot, tab="create"):
        """
        Make sure all checkboxes are off to start
        """
        assert tab in ["create", "transfer"]

        checkbox_names = list(canonical_folders.get_datatype_folders().keys())
        if tab == "create":
            checkboxes_id = "#create_folders_datatype_checkboxes"
        else:
            checkbox_names.extend(["all", "all_datatype", "all_non_datatype"])
            checkboxes_id = "#transfer_custom_datatype_checkboxes"

        for datatype in checkbox_names:
            id = f"#{tab}_{datatype}_checkbox"
            if pilot.app.screen.query_one(id).value:
                await self.change_checkbox(pilot, id)

        datatype_config = pilot.app.screen.query_one(
            checkboxes_id
        ).datatype_config
        assert all(val is False for val in datatype_config.values())

    async def exit_to_main_menu_and_reeneter_project_manager(
        self, pilot, project_name
    ):
        await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")
        assert pilot.app.screen.id == "_default"
        await self.check_and_click_onto_existing_project(pilot, project_name)

    async def close_messagebox(self, pilot):
        # for some reason clicking does not work...
        pilot.app.screen.on_button_pressed()
        await pilot.pause()

    # -------------------------------------------------------------------------
    # Test Create
    # -------------------------------------------------------------------------

    if False:

        @pytest.mark.asyncio
        async def test_create_folders_widgets_display(
            self, setup_project_paths
        ):
            """"""
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

            app = TuiApp()
            async with app.run_test() as pilot:

                await self.check_and_click_onto_existing_project(
                    pilot, project_name
                )

                assert (
                    pilot.app.screen.query_one(
                        "#create_folders_subject_label"
                    ).renderable._text[0]
                    == "Subject(s)"
                )
                assert (
                    pilot.app.screen.query_one(
                        "#create_folders_subject_input"
                    ).placeholder
                    == "e.g. sub-001"
                )

                assert (
                    pilot.app.screen.query_one(
                        "#tabscreen_session_label"
                    ).renderable._text[0]
                    == "Session(s)"
                )
                assert (
                    pilot.app.screen.query_one(
                        "#create_folders_session_input"
                    ).placeholder
                    == "e.g. ses-001"
                )

                assert (
                    pilot.app.screen.query_one(
                        "#create_folders_datatype_label"
                    ).renderable._text[0]
                    == "Datatype(s)"
                )

                assert (
                    pilot.app.screen.query_one(
                        "#create_behav_checkbox"
                    ).label._text[0]
                    == "Behav"
                )  # TODO: CHECK PERSISTENT SETTINGS
                assert (
                    pilot.app.screen.query_one(
                        "#create_ephys_checkbox"
                    ).label._text[0]
                    == "Ephys"
                )
                assert (
                    pilot.app.screen.query_one(
                        "#create_funcimg_checkbox"
                    ).label._text[0]
                    == "Funcimg"
                )
                assert (
                    pilot.app.screen.query_one(
                        "#create_anat_checkbox"
                    ).label._text[0]
                    == "Anat"
                )

                assert (
                    pilot.app.screen.query_one(
                        "#create_folders_create_folders_button"
                    ).label._text[0]
                    == "Create Folders"
                )
                assert (
                    pilot.app.screen.query_one(
                        "#create_folders_settings_button"
                    ).label._text[0]
                    == "Settings"
                )

        @pytest.mark.asyncio
        async def test_create_folders_bad_validation_tooltips(
            self, setup_project_paths
        ):
            # Not exhaustive
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
        async def test_get_next_sub_and_ses_no_template(
            self, setup_project_paths
        ):
            """"""
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
        async def test_fill_and_append_next_sub_and_ses(
            self, setup_project_paths
        ):
            """"""
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
                    == pilot.app.screen.query_one(
                        "#create_folders_directorytree"
                    )
                    .get_node_at_line(2)
                    .data.path.as_posix()
                )

        @pytest.mark.asyncio
        async def test_create_folders_directorytree_open_filesystem(
            self, setup_project_paths, monkeypatch
        ):  # TODO: these tests are getting a lot of boilerplate!! stupid await...
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
                    == pilot.app.screen.query_one(
                        "#create_folders_directorytree"
                    )
                    .get_node_at_line(3)
                    .data.path.as_posix()
                )

        # TOOD: check all settings widgets... check they change underlying persistent settings. Figure out how to tis thi sin with the rest of persistent settings tests
        # TODO: fully split out all 'widgets' tests.
        @pytest.mark.asyncio
        async def test_create_folders_settings_top_level_folder(
            self, setup_project_paths
        ):
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

            app = TuiApp()
            async with app.run_test() as pilot:
                await self.setup_existing_project_create_tab_filled_sub_and_ses(
                    pilot, project_name, create_folders=False
                )

                await self.scroll_to_click_pause(
                    pilot, "#create_folders_settings_button"
                )

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

            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
        async def test_create_folders_formatted_names(
            self, setup_project_paths
        ):
            # TODO: tidy this up, some horrible decisions!
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

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
                    pilot,
                    "#create_folders_session_input",
                    "ses-001@TO@003_@DATE@",
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
                        (project.cfg["local_path"] / "rawdata" / sub).glob(
                            "ses-*"
                        )
                    )

                    assert re.fullmatch(ses_1_regexp, ses_level_names[0].stem)
                    assert re.fullmatch(ses_2_regexp, ses_level_names[1].stem)
                    assert re.fullmatch(ses_3_regexp, ses_level_names[2].stem)

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

        # -------------------------------------------------------------------------
        # Tests
        # -------------------------------------------------------------------------

        @pytest.mark.asyncio
        @pytest.mark.parametrize("kwargs_set", [1, 2])
        async def test_make_new_project_configs(
            self,
            empty_project_paths,
            kwargs_set,
        ):
            """
            Check the ConfigsContent when making a new project. This contains
            many widgets shared with the ConfigsContent on the tab page, however also
            includes an additional information banner and input for the project name.

            Here check these widgets are display correctly, and fill them. Next
            check the config widgets are empty, then fill the widgets, save,
            and check the interface.project and saved configs match the new
            settings.
            """
            tmp_config_path, tmp_path, project_name = (
                empty_project_paths.values()
            )  # TODO: use dict

            kwargs = {
                "local_path": (tmp_path / "local" / project_name).as_posix(),
                # not used in TUI, set to `make_config_file` defaults.
                "central_path": (
                    tmp_path / "central" / project_name
                ).as_posix(),
                "show_transfer_progress": False,
            }

            if kwargs_set == 1:
                kwargs.update(
                    {
                        "connection_method": "local_filesystem",
                        "central_host_id": None,
                        "central_host_username": None,
                        "overwrite_old_files": False,
                    }
                )
            elif kwargs_set == 2:
                kwargs.update(
                    {
                        "connection_method": "ssh",
                        "central_host_id": "@test.host.id",
                        "central_host_username": "test_username",
                        "overwrite_old_files": True,
                    }
                )

            Path(kwargs["local_path"]).parent.mkdir(parents=True)
            Path(kwargs["central_path"]).parent.mkdir(parents=True)

            app = TuiApp()
            async with app.run_test() as pilot:

                # Select a new project, check NewProjectScreen is displayed correctly.
                await pilot.click("#mainwindow_new_project_button")
                await pilot.pause()

                assert pilot.app.screen_stack[0].id == "_default"
                assert isinstance(pilot.app.screen_stack[1], NewProjectScreen)
                assert pilot.app.screen_stack[1].title == "Make New Project"

                # Get the ConfigsContent and check all configs are displayed correctly.
                # `check_new_project_configs` checks empty defaults are displayed,
                # then updates with the kwargs and checks.
                configs_content = pilot.app.screen.query_one(
                    "#new_project_configs_content"
                )

                await self.check_new_project_configs(
                    pilot, project_name, configs_content, kwargs
                )

                # Save the configs and check the correct messages are shown.
                await self.scroll_to_click_pause(
                    pilot,
                    "#configs_save_configs_button",
                )

                assert (
                    pilot.app.screen.query_one(
                        "#messagebox_message_label"
                    ).renderable._text[0]
                    == "A DataShuttle project has now been created.\n\n Click 'OK' to "
                    "proceed to the project page, where you will be able to create and "
                    "transfer project folders."
                )

                # for some reason clicking does not work...
                pilot.app.screen.on_button_pressed()
                await pilot.pause()

                assert isinstance(pilot.app.screen, ProjectManagerScreen)

                # After saving, check all configs are correct on the DataShuttle
                # instance as well as the stored configs.
                test_utils.check_configs(
                    pilot.app.screen.interface.project,
                    kwargs,
                    tmp_config_path / project_name / "config.yaml",
                )
                assert (
                    pilot.app.screen.interface.project.project_name
                    == project_name
                )

        async def check_new_project_configs(
            self, pilot, project_name, configs_content, kwargs
        ):
            """
            Check the configs displayed on the TUI match those founds in `kwargs`.
            Also, check the widgets unique to ConfigsContent on the configs selection
            for a new project.
            """
            # New Project Labels --------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_banner_label"
                ).renderable._text[0]
                == "Configure A New Project"
            )
            assert (
                configs_content.query_one(
                    "#configs_info_label"
                ).renderable._text[0]
                == "Set your configurations for a new project. For more details on "
                "each section,\nsee the Datashuttle documentation. Once configs "
                "are set, you will be able\nto use the 'Create' and 'Transfer' tabs."
            )

            # Project Name --------------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_name_label"
                ).renderable._text[0]
                == "Project Name"
            )
            assert configs_content.query_one("#configs_name_input").value == ""

            await self.fill_input(pilot, "#configs_name_input", project_name)
            assert (
                configs_content.query_one("#configs_name_input").value
                == project_name
            )

            # Shared Config Widgets -----------------------------------------------

            default_kwargs = {
                "local_path": "",
                "central_path": "",
                "connection_method": "local_filesystem",
                "overwrite_old_files": False,
            }
            await self.check_configs_widgets_match_configs(
                configs_content, default_kwargs
            )
            await self.set_configs_content_widgets(
                pilot, configs_content, kwargs
            )
            await self.check_configs_widgets_match_configs(
                configs_content, kwargs
            )

        @pytest.mark.asyncio
        async def test_configs_select_path(self, monkeypatch):
            """
            Test the 'Select' buttons / DirectoryTree on the ConfigsContent.
            These are used to select folders that are filled into the Input.
            Open the select dialog, select a folder, check the path is
            filled into the Input. There is one for both local
            and central path.

            When SSH is selected, the central path 'Select' should be disabled,
            as it only makes sense to choose this for local filesystem transfer.
            """
            self.monkeypatch_print(monkeypatch)

            app = TuiApp()
            async with app.run_test() as pilot:

                # Select the page and ConfigsContent for setting up new project
                await pilot.click("#mainwindow_new_project_button")
                await pilot.pause()

                configs_content = pilot.app.screen.query_one(
                    "#new_project_configs_content"
                )

                local_path_button = pilot.app.screen.query_one(
                    "#configs_local_path_select_button"
                )
                central_path_button = pilot.app.screen.query_one(
                    "#configs_central_path_select_button"
                )

                # For central and local path selects, click the button, select
                # the first folder from the DirectoryTree and check the input is filled.
                for select_button, path_input_id in zip(
                    [local_path_button, central_path_button],
                    [
                        "#configs_local_path_input",
                        "#configs_central_path_input",
                    ],
                ):
                    await self.scroll_to_click_pause(
                        pilot,
                        f"#{select_button.id}",
                    )

                    assert isinstance(
                        pilot.app.screen, SelectDirectoryTreeScreen
                    )

                    tree = pilot.app.screen.query_one(
                        "#select_directory_tree_directory_tree"
                    )
                    root_path = tree.root.data.path

                    import time

                    pilot.app.screen.prev_click_time = time.time()
                    pilot.app.screen.on_directory_tree_directory_selected(
                        tree.root.data
                    )
                    await pilot.pause()

                    assert (
                        configs_content.query_one(path_input_id).value
                        == root_path.as_posix()
                    )

                    await pilot.pause()

                # Check the central path only is disabled in SSH mode.
                assert local_path_button.disabled is False
                assert central_path_button.disabled is False

                await self.scroll_to_click_pause(
                    pilot, "#configs_ssh_radiobutton"
                )

                assert local_path_button.disabled is False
                assert central_path_button.disabled is True

        @pytest.mark.asyncio
        async def test_update_config_on_project_manager_screen(
            self, setup_project_paths
        ):
            """
            Test the ConfigsContent on the project manager tab screen.
            The project is set up in the fixture, navigate to the project page.
            Check that the default configs are displayed. Change all the configs,
            save, and check these are updated on the config file and on the
            `project` stored in `interface`.

            Next, exit out of the project with the "Main Menu" button, go back
            into the project and check the new configs are displayed.
            """
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

            app = TuiApp()
            async with app.run_test() as pilot:

                # Navigate to the existing project and click onto the
                # configs tab.
                await self.check_and_click_onto_existing_project(
                    pilot, project_name
                )

                await pilot.click(
                    f"Tab#{ContentTab.add_prefix('tabscreen_configs_tab')}"
                )

                configs_content = pilot.app.screen.query_one(
                    "#tabscreen_configs_content"
                )

                # Now get the default datashuttle configs, and check they match
                # those displayed on the ConfigsContent.
                project_cfg = copy.deepcopy(
                    pilot.app.screen.interface.project.cfg
                )
                project_cfg.convert_str_and_pathlib_paths(
                    project_cfg, "path_to_str"
                )  # TODO: this syntax is so weird.

                await self.check_configs_widgets_match_configs(
                    configs_content, project_cfg
                )

                # Now we make some new settings, and set the ConfigsContent.
                # Make sure they are all different to the existing configs,
                # then save and check the configs on the DataShuttle instance
                # and file are updated.
                local_path = tmp_path / f"some-random-path/{project_name}"
                central_path = tmp_path / f"some-random-path2/{project_name}"

                local_path.mkdir(parents=True)
                central_path.mkdir(parents=True)

                new_kwargs = {
                    "local_path": local_path.as_posix(),
                    "central_path": central_path.as_posix(),
                    "connection_method": "ssh",
                    "central_host_id": "random_host",
                    "central_host_username": "random_username",
                    "overwrite_old_files": True,
                }

                for key in new_kwargs.keys():
                    # The purpose is to update to completely new configs
                    assert new_kwargs[key] != project_cfg[key]

                await self.set_configs_content_widgets(
                    pilot, configs_content, new_kwargs
                )

                await self.check_configs_widgets_match_configs(
                    configs_content, new_kwargs
                )

                await self.scroll_to_click_pause(
                    pilot,
                    "#configs_save_configs_button",
                )
                assert (
                    pilot.app.screen.query_one(
                        "#messagebox_message_label"
                    ).renderable._text[0]
                    == "Configs saved."
                )

                # for some reason clicking does not work...
                pilot.app.screen.on_button_pressed()
                await pilot.pause()

                test_utils.check_configs(
                    pilot.app.screen.interface.project,
                    new_kwargs,
                    tmp_config_path / project_name / "config.yaml",
                )

                # Finally, use "Main Menu" button to go back to the home screen,
                # navigate back to the project and check the new configs are now
                # displayed.
                await self.scroll_to_click_pause(
                    pilot, "#all_main_menu_buttons"
                )
                assert pilot.app.screen.id == "_default"

                await self.check_and_click_onto_existing_project(
                    pilot, project_name
                )
                await pilot.click(
                    f"Tab#{ContentTab.add_prefix('tabscreen_configs_tab')}"
                )
                configs_content = pilot.app.screen.query_one(
                    "#tabscreen_configs_content"
                )
                await self.check_configs_widgets_match_configs(
                    configs_content, new_kwargs
                )
                await pilot.pause()

        # -------------------------------------------------------------------------
        # Helpers
        # -------------------------------------------------------------------------

        async def check_configs_widgets_match_configs(
            self, configs_content, kwargs
        ):
            """
            Check that the widgets of the TUI configs match those found
            in `kwargs`.
            """

            # Local Path ----------------------------------------------------------

            assert (
                configs_content.query_one("#configs_local_path_input").value
                == kwargs["local_path"]
            )

            # Connection Method ---------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_connect_method_label"
                ).renderable._text[0]
                == "Connection Method"
            )

            label = (
                "SSH"
                if kwargs["connection_method"] == "ssh"
                else "Local Filesystem"
            )
            assert (
                configs_content.query_one(
                    "#configs_connect_method_radioset"
                ).pressed_button.label._text[0]
                == label
            )

            if kwargs["connection_method"] == "ssh":

                # Central Host ID -------------------------------------------------

                assert (
                    configs_content.query_one(
                        "#configs_central_host_id_label"
                    ).renderable._text[0]
                    == "Central Host ID"
                )
                assert (
                    configs_content.query_one(
                        "#configs_central_host_id_input"
                    ).value
                    == kwargs["central_host_id"]
                )

                # Central Host Username -------------------------------------------

                assert (
                    configs_content.query_one(
                        "#configs_central_host_username_label"
                    ).renderable._text[0]
                    == "Central Host Username"
                )
                assert (
                    configs_content.query_one(
                        "#configs_central_host_username_input"
                    ).value
                    == kwargs["central_host_username"]
                )

                ssh_widgets_display = True
            else:
                ssh_widgets_display = False

            # SSH widget display --------------------------------------------------

            for id in [
                "#configs_central_host_id_label",
                "#configs_central_host_id_input",
                "#configs_central_host_username_label",
                "#configs_central_host_username_input",
            ]:
                assert (
                    configs_content.query_one(id).display
                    is ssh_widgets_display
                )

            # Central Path --------------------------------------------------------

            assert (
                configs_content.query_one("#configs_central_path_input").value
                == kwargs["central_path"]
            )

            # Transfer Options ----------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_transfer_options_container"
                ).border_title
                == "Transfer Options"
            )

            # Overwrite Old Files -------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_overwrite_files_checkbox"
                ).label._text[0]
                == "Overwrite Old Files"
            )

            assert (
                configs_content.query_one(
                    "#configs_overwrite_files_checkbox"
                ).value
                is kwargs["overwrite_old_files"]
            )

        async def set_configs_content_widgets(
            self, pilot, configs_content, kwargs
        ):
            """
            Given a dict of options that can be set on the configs TUI
            in kwargs, set all configs widgets according to kwargs.
            """

            # Local Path ----------------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_local_path_label"
                ).renderable._text[0]
                == "Local Path"
            )

            await self.fill_input(
                pilot, "#configs_local_path_input", kwargs["local_path"]
            )

            # Connection Method ---------------------------------------------------

            if kwargs["connection_method"] == "ssh":

                await self.scroll_to_click_pause(
                    pilot, "#configs_ssh_radiobutton"
                )

                # Central Host ID -------------------------------------------------

                await self.fill_input(
                    pilot,
                    "#configs_central_host_id_input",
                    kwargs["central_host_id"],
                )

                # Central Host Username -------------------------------------------

                await self.fill_input(
                    pilot,
                    "#configs_central_host_username_input",
                    kwargs["central_host_username"],
                )

            # Central Path --------------------------------------------------------

            configs_content.query_one("#configs_central_path_input").value = ""

            await self.fill_input(
                pilot, "#configs_central_path_input", kwargs["central_path"]
            )

            # Overwrite Files -----------------------------------------------------

            if kwargs["overwrite_old_files"]:

                await self.scroll_to_click_pause(
                    pilot,
                    "#configs_overwrite_files_checkbox",
                )

        # FAILED TO IMPLEMENT
        @pytest.mark.asyncio
        async def __test_create_folders_directorytree_reload(
            self, setup_project_paths
        ):
            # TODO: this is not possible to implement because in test environemnt
            # we need fully refresh the tree just to be able to access it, not sure
            # this this this.
            pass
            tmp_config_path, tmp_path, project_name = (
                setup_project_paths.values()
            )

            app = TuiApp()
            async with app.run_test() as pilot:
                await self.setup_existing_project_create_tab_filled_sub_and_ses(
                    pilot, project_name, create_folders=True
                )

                await self.reload_tree_nodes(
                    pilot, "#create_folders_directorytree", 4
                )

                (
                    pilot.app.screen.interface.project.cfg["local_path"]
                    / "rawdata"
                    / "sub-002"
                ).mkdir()

                await self.reload_tree_nodes(
                    pilot, "#create_folders_directorytree", 4
                )

                assert (
                    pilot.app.screen.query_one("#create_folders_directorytree")
                    .get_node_at_line(2)
                    .label._text[0]
                    == "sub-001"
                )
                assert (
                    pilot.app.screen.query_one("#create_folders_directorytree")
                    .get_node_at_line(8)
                    .label._text[0]
                    is None
                )
                breakpoint()

                await self.press_tree(
                    pilot,
                    "#create_folders_directorytree",
                    press_string="ctrl+r",
                )
                await self.reload_tree_nodes(
                    pilot, "#create_folders_directorytree", 10
                )

                breakpoint()  # TOOD: try and remove the above
                assert (
                    pilot.app.screen.query_one("#create_folders_directorytree")
                    .get_node_at_line(2)
                    .label._text[0]
                    == "sub-001"
                )
                assert (
                    pilot.app.screen.query_one("#create_folders_directorytree")
                    .get_node_at_line(8)
                    .label._text[0]
                    == "sub-002"
                )
