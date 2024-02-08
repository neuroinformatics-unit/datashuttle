import pytest
from textual.widgets._tabbed_content import ContentTab

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

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.create_folder_settings import (
    CreateFoldersSettingsScreen,
)
from datashuttle.tui.screens.new_project import NewProjectScreen


class TestTuiWidgets(TuiBase):

    #         self.name_templates: Dict = {}
    #         self.tui_settings: Dict = {}

    # Plan configs
    # Plan rest of create
    # Plan settings and behind the scenes TUI

    # 1) Do Configs
    # 2) Do Settings

    # -------------------------------------------------------------------------
    # Test Configs New Project
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_new_project_configs(self, empty_project_paths):

        tmp_config_path, tmp_path, project_name = empty_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            # Select a new project, check NewProjectScreen is displayed correctly.
            await pilot.click("#mainwindow_new_project_button")
            await pilot.pause()

            assert pilot.app.screen_stack[0].id == "_default"
            assert isinstance(pilot.app.screen_stack[1], NewProjectScreen)
            assert pilot.app.screen_stack[1].title == "Make New Project"

            configs_content = pilot.app.screen.query_one(
                "#new_project_configs_content"
            )

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
            assert (
                configs_content.query_one("#configs_name_input").placeholder
                == "e.g. my_first_project"
            )

            # Local Path ----------------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_local_path_label"
                ).renderable._text[0]
                == "Local Path"
            )
            assert (
                configs_content.query_one("#configs_local_path_input").value
                == ""
            )
            assert (
                configs_content.query_one(
                    "#configs_local_path_input"
                ).placeholder
                == "e.g. C:\\path\\to\\local\\my_projects\\my_first_project"
            )

            # Connection Method ---------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_connect_method_label"
                ).renderable._text[0]
                == "Connection Method"
            )
            assert (
                configs_content.query_one(
                    "#configs_connect_method_radioset"
                ).pressed_button.label._text[0]
                == "Local Filesystem"
            )

            # Central Path (Local Filesystem) ------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_central_path_label"
                ).renderable._text[0]
                == "Central Path"
            )
            assert (
                configs_content.query_one("#configs_central_path_input").value
                == ""
            )
            assert (
                configs_content.query_one(
                    "#configs_central_path_input"
                ).placeholder
                == "e.g. C:\\path\\to\\central\\my_projects\\my_first_project"
            )

            # Check Non SSH widgets hidden / disabled ----------------------------------
            await self.check_ssh_widgets(configs_content, ssh_on=False)

            # Change to SSH
            await self.scroll_to_click_pause(pilot, "#configs_ssh_radiobutton")
            await self.check_ssh_widgets(configs_content, ssh_on=True)

            # Central Path (SSH) ------------------------------------------

            assert (
                configs_content.query_one("#configs_central_path_input").value
                == ""
            )
            assert (
                configs_content.query_one(
                    "#configs_central_path_input"
                ).placeholder
                == "e.g. /nfs/path_on_server/myprojects/central"
            )

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
                == ""
            )
            assert (
                configs_content.query_one(
                    "#configs_central_host_id_input"
                ).placeholder
                == "e.g. ssh.swc.ucl.ac.uk"
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
                == ""
            )
            assert (
                configs_content.query_one(
                    "#configs_central_host_username_input"
                ).placeholder
                == "e.g. username"
            )

            # Transfer Options Container -----------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_transfer_options_container"
                ).border_title
                == "Transfer Options"
            )

            # Overwrite Old Files Checkbox ---------------------------------------------

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
                is False
            )

    async def check_ssh_widgets(self, configs_content, ssh_on):
        """"""
        assert (
            configs_content.query_one(
                "#configs_setup_ssh_connection_button"
            ).disabled
            is not ssh_on
        )
        assert (
            configs_content.query_one(
                "#configs_central_path_select_button"
            ).disabled
            is ssh_on
        )

        for id in [
            "#configs_central_host_id_label",
            "#configs_central_host_id_input",
            "#configs_central_host_username_label",
            "#configs_central_host_username_input",
        ]:
            assert configs_content.query_one(id).display is ssh_on

    # TODO: can crash ssh setup on new project configs

    # Also test the select at the end..

    # -------------------------------------------------------------------------
    # Test Configs Existing Project
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_existing_project_configs(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

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

            for id in [
                "#configs_info_label",
                "#configs_banner_label",
                "#configs_name_label",
                "#configs_name_input",
            ]:
                with pytest.raises(BaseException) as e:
                    configs_content.query_one(id)
                assert "No nodes match" in str(e)

    # -------------------------------------------------------------------------
    # Test Create
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_folders_widgets_display(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

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

    # -------------------------------------------------------------------------
    # Test Create Settings
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_folder_settings_widgets(self, setup_project_paths):
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
                pilot.app.screen.query_one(
                    "#create_folders_settings_toplevel_label"
                ).renderable._text[0]
                == "Top level folder:"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_settings_toplevel_select"
                ).value
                == "rawdata"
            )

            assert (
                pilot.app.screen.query_one(
                    "#create_folders_settings_bypass_validation_checkbox"
                ).label._text[0]
                == "Bypass validation"
            )
            assert (
                pilot.app.screen.query_one(
                    "#create_folders_settings_bypass_validation_checkbox"
                ).value
                is False
            )

            assert (
                pilot.app.screen.query_one(
                    "#template_settings_validation_on_checkbox"
                ).label._text[0]
                == "Template Validation"
            )
            assert (
                pilot.app.screen.query_one(
                    "#template_settings_validation_on_checkbox"
                ).value
                is False
            )

            await self.scroll_to_click_pause(
                pilot, "#template_settings_validation_on_checkbox"
            )

            # TODO: fix the below
            assert (
                pilot.app.screen.query_one(
                    "#template_message_label"
                ).renderable._text[0]
                == "\n        A 'Template' can be set check subject or session names are\n        formatted in a specific way.\n\n        For example:\n            sub-\\d\\d_id-.?.?.?_.*\n\n        Visit the Documentation for more information.\n        "
            )

            assert (
                pilot.app.screen.query_one(
                    "#template_settings_radioset"
                ).pressed_button.label._text[0]
                == "Subject"
            )
            assert (
                pilot.app.screen.query_one("#template_settings_input").value
                == ""
            )
            assert (
                pilot.app.screen.query_one(
                    "#template_settings_input"
                ).placeholder
                == "sub-"
            )

            await self.scroll_to_click_pause(
                pilot, "#template_settings_session_radiobutton"
            )
            assert (
                pilot.app.screen.query_one("#template_settings_input").value
                == ""
            )
            assert (
                pilot.app.screen.query_one(
                    "#template_settings_input"
                ).placeholder
                == "ses-"
            )

    @pytest.mark.asyncio
    async def __test_all_top_level_folder_selects(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=False
            )
            await self.scroll_to_click_pause(
                pilot, "#create_folders_settings_button"
            )

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
            # CHECK FILE

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
            # CHECK FILE
            breakpoint()

            # Close and open
            # Then do the same for all others

            # TODO: MOVE, also check the saved file! critical!

    async def check_all_top_level_selects(
        self, pilot, create_val, transfer_toplevel_val, transfer_custom_val
    ):

        assert (
            pilot.app.screen.interface.tui_settings["top_level_folder_select"][
                "create_tab"
            ]
            == "derivatives"
        )
        assert (
            pilot.app.screen.query_one(
                "#create_folders_settings_toplevel_select"
            ).value
            == "derivatives"
        )

    # test transfer widgets

    # test top level folder & settings here
    # Test checkboxes (create and custom transfer) and underlying settings here

    # Test validation on other tests
    # Test name templates on other tests
    # Test name templates settings here?

    # Check on transfer tabs
    # Check on file

    # -------------------------------------------------------------------------
    # Test Global Settings Settings
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Test Transfer
    # -------------------------------------------------------------------------

    # TEST PERSISTENT SETTINGS

    # CREATE

    # TRANFSER CUSTOM

    # SELECT WIDGETS

    # TEST GLOBAL SETTINGS
