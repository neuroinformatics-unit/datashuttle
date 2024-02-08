import pytest

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


class TestTuiWidgets(TuiBase):

    # -------------------------------------------------------------------------
    # Test Configs New Project
    # -------------------------------------------------------------------------

    # Also test the select at the end..

    # -------------------------------------------------------------------------
    # Test Configs Existing Project
    # -------------------------------------------------------------------------

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
