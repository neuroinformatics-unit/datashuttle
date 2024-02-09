import pytest
import test_utils
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
# TODO: need to add bypass validation and new configs in datashuttle itself. to generate d.s. tests, as well as new persistent settings?
# TODO: need to check validation and other persistent settings? name t empaltes? genera settings persistent settings!??!?!?!?
# TODO: couble click to add next, ctrl for generic validation
# TODO: there is a deep reason that sub and ses need to be validate together - to check for ses duplicates within sub ...

from tui_base import TuiBase

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.create_folder_settings import (
    CreateFoldersSettingsScreen,
)
from datashuttle.tui.screens.new_project import NewProjectScreen


class TestTuiWidgets(TuiBase):
    """
    Explain logic of this class...
    """

    # -------------------------------------------------------------------------
    # Test Configs New Project
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_new_project_configs(self, empty_project_paths):

        app = TuiApp()
        async with app.run_test() as pilot:

            # Select a new project, check NewProjectScreen is displayed correctly.
            await pilot.click("#mainwindow_new_project_button")
            await pilot.pause()

            assert pilot.app.screen_stack[0].id == "_default"
            assert isinstance(pilot.app.screen_stack[1], NewProjectScreen)
            assert pilot.app.screen_stack[1].title == "Make New Project"

            configs_content = pilot.app.screen.query_one("#new_project_configs_content")

            # New Project Labels --------------------------------------------------

            assert configs_content.query_one("#configs_banner_label").renderable._text[0] == "Configure A New Project"
            assert configs_content.query_one("#configs_info_label").renderable._text[0] == "Set your configurations for a new project. For more details on " "each section,\nsee the Datashuttle documentation. Once configs " "are set, you will be able\nto use the 'Create' and 'Transfer' tabs."

            # Project Name --------------------------------------------------------

            assert configs_content.query_one("#configs_name_label").renderable._text[0] == "Project Name"
            assert configs_content.query_one("#configs_name_input").value == ""
            assert configs_content.query_one("#configs_name_input").placeholder == "e.g. my_first_project"

            # Local Path ----------------------------------------------------------

            assert configs_content.query_one("#configs_local_path_label").renderable._text[0] == "Local Path"
            assert configs_content.query_one("#configs_local_path_input").value == ""
            assert configs_content.query_one("#configs_local_path_input").placeholder == "e.g. C:\\path\\to\\local\\my_projects\\my_first_project"

            # Connection Method ---------------------------------------------------

            assert configs_content.query_one("#configs_connect_method_label").renderable._text[0] == "Connection Method"
            assert configs_content.query_one("#configs_connect_method_radioset").pressed_button.label._text[0] == "Local Filesystem"

            # Central Path (Local Filesystem) ------------------------------------------

            assert configs_content.query_one("#configs_central_path_label").renderable._text[0] == "Central Path"
            assert configs_content.query_one("#configs_central_path_input").value == ""
            assert configs_content.query_one("#configs_central_path_input").placeholder == "e.g. C:\\path\\to\\central\\my_projects\\my_first_project"

            # Check Non SSH widgets hidden / disabled ----------------------------------
            await self.check_ssh_widgets(configs_content, ssh_on=False)

            # Change to SSH
            await self.scroll_to_click_pause(pilot, "#configs_ssh_radiobutton")
            await self.check_ssh_widgets(configs_content, ssh_on=True)

            # Central Path (SSH) ------------------------------------------

            assert configs_content.query_one("#configs_central_path_input").value == ""
            assert configs_content.query_one("#configs_central_path_input").placeholder == "e.g. /nfs/path_on_server/myprojects/central"

            # Central Host ID -------------------------------------------------

            assert configs_content.query_one("#configs_central_host_id_label").renderable._text[0] == "Central Host ID"
            assert configs_content.query_one("#configs_central_host_id_input").value == ""
            assert configs_content.query_one("#configs_central_host_id_input").placeholder == "e.g. ssh.swc.ucl.ac.uk"

            # Central Host Username -------------------------------------------

            assert configs_content.query_one("#configs_central_host_username_label").renderable._text[0] == "Central Host Username"
            assert configs_content.query_one("#configs_central_host_username_input").value == ""
            assert configs_content.query_one("#configs_central_host_username_input").placeholder == "e.g. username"

            # Transfer Options Container -----------------------------------------------

            assert configs_content.query_one("#configs_transfer_options_container").border_title == "Transfer Options"

            # Overwrite Old Files Checkbox ---------------------------------------------

            assert configs_content.query_one("#configs_overwrite_files_checkbox").label._text[0] == "Overwrite Old Files"
            assert configs_content.query_one("#configs_overwrite_files_checkbox").value is False

            await pilot.pause()

    async def check_ssh_widgets(self, configs_content, ssh_on):
        """"""
        assert configs_content.query_one("#configs_setup_ssh_connection_button").disabled is not ssh_on
        assert configs_content.query_one("#configs_central_path_select_button").disabled is ssh_on

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
            await self.check_and_click_onto_existing_project(pilot, project_name)
            await pilot.click(f"Tab#{ContentTab.add_prefix('tabscreen_configs_tab')}")
            configs_content = pilot.app.screen.query_one("#tabscreen_configs_content")

            for id in [
                "#configs_info_label",
                "#configs_banner_label",
                "#configs_name_label",
                "#configs_name_input",
            ]:
                with pytest.raises(BaseException) as e:
                    configs_content.query_one(id)
                assert "No nodes match" in str(e)

            await pilot.pause()

    # -------------------------------------------------------------------------
    # Test Create
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_folders_widgets_display(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(pilot, project_name)

            assert pilot.app.screen.query_one("#create_folders_subject_label").renderable._text[0] == "Subject(s)"
            assert pilot.app.screen.query_one("#create_folders_subject_input").placeholder == "e.g. sub-001"

            assert pilot.app.screen.query_one("#tabscreen_session_label").renderable._text[0] == "Session(s)"
            assert pilot.app.screen.query_one("#create_folders_session_input").placeholder == "e.g. ses-001"

            assert pilot.app.screen.query_one("#create_folders_datatype_label").renderable._text[0] == "Datatype(s)"

            assert pilot.app.screen.query_one("#create_behav_checkbox").label._text[0] == "Behav"  # TODO: CHECK PERSISTENT SETTINGS
            assert pilot.app.screen.query_one("#create_ephys_checkbox").label._text[0] == "Ephys"
            assert pilot.app.screen.query_one("#create_funcimg_checkbox").label._text[0] == "Funcimg"
            assert pilot.app.screen.query_one("#create_anat_checkbox").label._text[0] == "Anat"

            assert pilot.app.screen.query_one("#create_folders_create_folders_button").label._text[0] == "Create Folders"
            assert pilot.app.screen.query_one("#create_folders_settings_button").label._text[0] == "Settings"

            await pilot.pause()

    # -------------------------------------------------------------------------
    # Test Create Settings
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_folder_settings_widgets(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.setup_existing_project_create_tab_filled_sub_and_ses(pilot, project_name, create_folders=False)
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")

            assert isinstance(pilot.app.screen, CreateFoldersSettingsScreen)

            assert pilot.app.screen.query_one("#create_folders_settings_toplevel_label").renderable._text[0] == "Top level folder:"
            assert pilot.app.screen.query_one("#create_folders_settings_toplevel_select").value == "rawdata"

            assert pilot.app.screen.query_one("#create_folders_settings_bypass_validation_checkbox").label._text[0] == "Bypass validation"
            assert pilot.app.screen.query_one("#create_folders_settings_bypass_validation_checkbox").value is False

            assert pilot.app.screen.query_one("#template_settings_validation_on_checkbox").label._text[0] == "Template Validation"
            assert pilot.app.screen.query_one("#template_settings_validation_on_checkbox").value is False

            assert pilot.app.screen.query_one("#template_inner_container").disabled is True
            await self.scroll_to_click_pause(pilot, "#template_settings_validation_on_checkbox")
            assert pilot.app.screen.query_one("#template_inner_container").disabled is False

            assert " A 'Template' can be set check subject or session names" in pilot.app.screen.query_one("#template_message_label").renderable._text[0]

            assert pilot.app.screen.query_one("#template_settings_radioset").pressed_button.label._text[0] == "Subject"
            assert pilot.app.screen.query_one("#template_settings_input").value == ""
            assert pilot.app.screen.query_one("#template_settings_input").placeholder == "sub-"

            await self.scroll_to_click_pause(pilot, "#template_settings_session_radiobutton")
            assert pilot.app.screen.query_one("#template_settings_input").value == ""
            assert pilot.app.screen.query_one("#template_settings_input").placeholder == "ses-"

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_name_templates_widgets_and_settings(self, setup_project_paths):

        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        sub_regexp = "sub-\d\d\d"
        ses_regexp = "ses-00\d_????"

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.setup_existing_project_create_tab_filled_sub_and_ses(pilot, project_name, create_folders=False)

            # Check the default template settings are as expected
            expected_template = {"on": False, "sub": None, "ses": None}
            assert pilot.app.screen.interface.get_name_templates() == expected_template
            assert pilot.app.screen.interface.project.get_name_templates() == expected_template

            # Go to the Settings window, turn on validation and fill a sub regexp
            # into the Input
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")

            await self.scroll_to_click_pause(pilot, "#template_settings_validation_on_checkbox")
            await self.fill_input(pilot, "#template_settings_input", sub_regexp)

            # Close the window and check the template settings are stored as expected
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_close_button")

            expected_template = {"on": True, "sub": sub_regexp, "ses": None}
            assert pilot.app.screen.interface.get_name_templates() == expected_template
            assert pilot.app.screen.interface.project.get_name_templates() == expected_template

            # Refresh the project and check settings have persisted
            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)

            assert pilot.app.screen.interface.get_name_templates() == expected_template
            assert pilot.app.screen.interface.project.get_name_templates() == expected_template

            # Go back onto the Settings window and explore more options - enter a
            # subject regexp and turn the templates off, then close and check
            # all settings are as expected.
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")
            assert pilot.app.screen.query_one("#template_settings_validation_on_checkbox").value is True
            assert pilot.app.screen.query_one("#template_settings_input").value == sub_regexp

            await self.scroll_to_click_pause(pilot, "#template_settings_session_radiobutton")
            assert pilot.app.screen.query_one("#template_settings_input").value == ""

            await self.fill_input(pilot, "#template_settings_input", ses_regexp)
            await self.scroll_to_click_pause(pilot, "#template_settings_validation_on_checkbox")
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_close_button")

            expected_template = {"on": False, "sub": sub_regexp, "ses": ses_regexp}
            assert pilot.app.screen.interface.get_name_templates() == expected_template
            assert pilot.app.screen.interface.project.get_name_templates() == expected_template

            # Refresh the project and do a final check all settings have persisted and
            # are updated correctly on the TUI.
            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)
            assert pilot.app.screen.interface.get_name_templates() == expected_template
            assert pilot.app.screen.interface.project.get_name_templates() == expected_template

            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")
            assert pilot.app.screen.query_one("#template_settings_validation_on_checkbox").value is False
            assert pilot.app.screen.query_one("#template_settings_input").value == sub_regexp

            await self.scroll_to_click_pause(pilot, "#template_settings_validation_on_checkbox")
            await self.scroll_to_click_pause(pilot, "#template_settings_session_radiobutton")
            assert pilot.app.screen.query_one("#template_settings_input").value == ses_regexp

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_bypass_validation_settings(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.setup_existing_project_create_tab_filled_sub_and_ses(pilot, project_name, create_folders=False)
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")

            assert pilot.app.screen.query_one("#create_folders_settings_bypass_validation_checkbox").value is False
            assert pilot.app.screen.interface.project.get_bypass_validation() is False

            await self.scroll_to_click_pause(pilot, "#create_folders_settings_bypass_validation_checkbox")

            assert pilot.app.screen.query_one("#create_folders_settings_bypass_validation_checkbox").value is True
            assert pilot.app.screen.interface.project.get_bypass_validation() is True

            await self.scroll_to_click_pause(pilot, "#create_folders_settings_close_button")
            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")

            assert pilot.app.screen.query_one("#create_folders_settings_bypass_validation_checkbox").value is True
            assert pilot.app.screen.interface.project.get_bypass_validation() is True

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_all_top_level_folder_selects(self, setup_project_paths):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            # Open project, check top level folder are correct
            await self.setup_existing_project_create_tab_filled_sub_and_ses(pilot, project_name, create_folders=False)
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")

            await self.check_top_folder_select(
                pilot,
                "#create_folders_settings_toplevel_select",
                "create_tab",
                "rawdata",
                move_to_position=False,
            )
            await self.check_top_folder_select(
                pilot,
                "#create_folders_settings_toplevel_select",
                "create_tab",
                "derivatives",
                move_to_position=5,
            )

            # Exit project, return and check values are updated property
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_close_button")
            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)

            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")
            await self.check_top_folder_select(
                pilot,
                "#create_folders_settings_toplevel_select",
                "create_tab",
                "derivatives",
                move_to_position=5,
            )

            # Move to transfer tab top level folder option, perform the same actions,
            # checking create settings toplevel select is not changed
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_close_button")
            await self.scroll_to_click_pause(pilot, f"Tab#{ContentTab.add_prefix('tabscreen_transfer_tab')}")

            await self.scroll_to_click_pause(pilot, "#transfer_toplevel_radiobutton")
            await self.check_top_folder_select(
                pilot,
                "#transfer_toplevel_select",
                "toplevel_transfer",
                "rawdata",
                move_to_position=False,
            )
            await self.check_top_folder_select(
                pilot,
                "#transfer_toplevel_select",
                "toplevel_transfer",
                "derivatives",
                move_to_position=5,
            )

            # Now the same for custom
            await self.scroll_to_click_pause(pilot, "#transfer_custom_radiobutton")
            await self.check_top_folder_select(
                pilot,
                "#transfer_custom_select",
                "custom_transfer",
                "rawdata",
                move_to_position=False,
            )
            await self.check_top_folder_select(
                pilot,
                "#transfer_custom_select",
                "custom_transfer",
                "derivatives",
                move_to_position=5,
            )

            # Now go back to main menu, go back and check all are as expected and switch back to original value for good measure.
            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)

            # recheck create settings
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_button")
            await self.check_top_folder_select(
                pilot,
                "#create_folders_settings_toplevel_select",
                "create_tab",
                "derivatives",
                move_to_position=False,
            )
            await self.check_top_folder_select(
                pilot,
                "#create_folders_settings_toplevel_select",
                "create_tab",
                "rawdata",
                move_to_position=4,
            )

            # recheck transfer toplevel
            await self.scroll_to_click_pause(pilot, "#create_folders_settings_close_button")
            await self.scroll_to_click_pause(pilot, f"Tab#{ContentTab.add_prefix('tabscreen_transfer_tab')}")

            await self.scroll_to_click_pause(pilot, "#transfer_toplevel_radiobutton")
            await self.check_top_folder_select(
                pilot,
                "#transfer_toplevel_select",
                "toplevel_transfer",
                "derivatives",
                move_to_position=False,
            )
            await self.check_top_folder_select(
                pilot,
                "#transfer_toplevel_select",
                "toplevel_transfer",
                "rawdata",
                move_to_position=4,
            )

            # recheck transfer custom
            await self.scroll_to_click_pause(pilot, "#transfer_custom_radiobutton")
            await self.check_top_folder_select(
                pilot,
                "#transfer_custom_select",
                "custom_transfer",
                "derivatives",
                move_to_position=False,
            )
            await self.check_top_folder_select(
                pilot,
                "#transfer_custom_select",
                "custom_transfer",
                "rawdata",
                move_to_position=4,
            )

            await pilot.pause()

    async def check_top_folder_select(self, pilot, id, tab_name, expected_val, move_to_position: False):
        """
        If move to position is not False, must be int specifying position
        """
        if move_to_position:
            await pilot.click(id)
            await pilot.click(id, offset=(2, move_to_position))
            await pilot.pause()

        assert pilot.app.screen.interface.tui_settings["top_level_folder_select"][tab_name] == expected_val
        assert pilot.app.screen.query_one(id).value == expected_val

        assert pilot.app.screen.interface.project._load_persistent_settings()["tui"]["top_level_folder_select"][tab_name] == expected_val

    @pytest.mark.asyncio
    async def test_all_checkboxes(self, setup_project_paths):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(pilot, project_name)

            await self.turn_off_all_datatype_checkboxes(pilot)  # TODO: this is only for create

            # Cycle through all checkboxes, turning on sequentially and
            # checking all configs are correct.
            expected_create = test_utils.get_all_folders_used(value=False)

            for datatype in ["behav", "ephys", "funcimg", "anat"]:
                await self.change_checkbox(pilot, f"#create_{datatype}_checkbox")
                expected_create[datatype] = True
                self.check_datatype_checkboxes(pilot, "create", expected_create)

            # Now turn off an arbitary subset so they are not longer all on (which is default).
            # Reload the screen, and check the checkboxes are still correct.
            await self.change_checkbox(pilot, "#create_ephys_checkbox")
            await self.change_checkbox(pilot, "#create_anat_checkbox")
            expected_create = test_utils.get_all_folders_used(value=False)
            expected_create.update({"behav": True, "funcimg": True})

            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)

            self.check_datatype_checkboxes(pilot, "create", expected_create)

            # Now we got to custom transfer checkboxes and do the same.
            # These are done in the same test to check they don't interact in a weird way.
            await self.scroll_to_click_pause(pilot, f"Tab#{ContentTab.add_prefix('tabscreen_transfer_tab')}")
            await self.scroll_to_click_pause(pilot, "#transfer_custom_radiobutton")

            await self.turn_off_all_datatype_checkboxes(pilot, tab="transfer")

            expected_transfer = test_utils.get_all_folders_used(value=False)
            expected_transfer.update(
                {
                    "all": False,
                    "all_datatype": False,
                    "all_non_datatype": False,
                }
            )

            for datatype in [
                "behav",
                "ephys",
                "funcimg",
                "anat",
                "all",
                "all_datatype",
                "all_non_datatype",
            ]:
                await self.change_checkbox(pilot, f"#transfer_{datatype}_checkbox")
                expected_transfer[datatype] = True
                self.check_datatype_checkboxes(pilot, "transfer", expected_transfer)

            # Reload the screen, and check everything is as previously
            # set on both create and transfer tabs
            await self.exit_to_main_menu_and_reeneter_project_manager(pilot, project_name)

            self.check_datatype_checkboxes(pilot, "create", expected_create)

            await self.scroll_to_click_pause(pilot, f"Tab#{ContentTab.add_prefix('tabscreen_transfer_tab')}")
            await self.scroll_to_click_pause(pilot, "#transfer_custom_radiobutton")
            self.check_datatype_checkboxes(pilot, "create", expected_create)

            await pilot.pause()

    def check_datatype_checkboxes(self, pilot, tab, expected_on):
        """"""
        assert tab in ["create", "transfer"]
        if tab == "create":
            id = "#create_folders_datatype_checkboxes"
            dict_key = "create_checkboxes_on"
        else:
            id = "#transfer_custom_datatype_checkboxes"
            dict_key = "transfer_checkboxes_on"

        assert pilot.app.screen.query_one(id).datatype_config == expected_on
        assert pilot.app.screen.interface.tui_settings[dict_key] == expected_on
        assert pilot.app.screen.interface.project._load_persistent_settings()["tui"][dict_key] == expected_on


    # -------------------------------------------------------------------------
    # Test Transfer
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_all_transfer_widgets(self):
        # checkboxes are tested already
        # top level select are tested already

    # -------------------------------------------------------------------------
    # Test Logging
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Test Global Settings Settings
    # -------------------------------------------------------------------------
