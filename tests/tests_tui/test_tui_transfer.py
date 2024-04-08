import pytest
import test_utils
from tui_base import TuiBase

from datashuttle.tui.app import TuiApp


class TestTuiTransfer(TuiBase):
    """
    Test transferring through the TUI (entire project, top
    level only or custom). This class leverages the underlying
    test utils that check API transfers.
    """

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.asyncio
    async def test_transfer_entire_project(
        self, setup_project_paths, upload_or_download
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "transfer")

            project = pilot.app.screen.interface.project

            base_path_to_check = self.setup_project_for_data_transfer(
                project,
                subs,
                sessions,
                ["rawdata", "derivatives"],
                upload_or_download,
            )

            await self.run_transfer(pilot, upload_or_download)

            for top_level_folder in ["rawdata", "derivatives"]:
                test_utils.check_datatype_sub_ses_uploaded_correctly(
                    base_path_to_check / top_level_folder,
                    ["behav", "ephys", "funcimg", "anat"],
                    subs,
                    sessions,
                )

            await pilot.pause()

    @pytest.mark.parametrize("top_level_folder", ["rawdata", "derivatives"])
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.asyncio()
    async def test_transfer_top_level_folder(
        self, setup_project_paths, top_level_folder, upload_or_download
    ):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "transfer")
            await self.scroll_to_click_pause(
                pilot, "#transfer_toplevel_radiobutton"
            )
            project = pilot.app.screen.interface.project

            base_path_to_check = self.setup_project_for_data_transfer(
                project, subs, sessions, [top_level_folder], upload_or_download
            )

            await self.switch_top_level_folder_select(
                pilot, "#transfer_toplevel_select", top_level_folder
            )

            await self.run_transfer(pilot, upload_or_download)

            test_utils.check_working_top_level_folder_only_exists(
                top_level_folder,
                base_path_to_check / top_level_folder,
                subs,
                sessions,
            )
            await pilot.pause()

    @pytest.mark.parametrize("top_level_folder", ["rawdata", "derivatives"])
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.asyncio
    async def test_transfer_custom(
        self, setup_project_paths, top_level_folder, upload_or_download
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        sub_to_transfer = "sub-002"
        ses_to_transfer = "ses-003"

        app = TuiApp()
        async with app.run_test() as pilot:

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )
            await self.switch_tab(pilot, "transfer")
            await self.scroll_to_click_pause(
                pilot, "#transfer_custom_radiobutton"
            )
            project = pilot.app.screen.interface.project

            base_path_to_check = self.setup_project_for_data_transfer(
                project, subs, sessions, [top_level_folder], upload_or_download
            )

            await self.switch_top_level_folder_select(
                pilot, "#transfer_custom_select", top_level_folder
            )

            await self.fill_input(
                pilot, "#transfer_subject_input", sub_to_transfer
            )

            await self.fill_input(
                pilot, "#transfer_session_input", ses_to_transfer
            )

            await self.scroll_to_click_pause(
                pilot, "#transfer_all_checkbox"
            )  # turn this off

            await self.scroll_to_click_pause(
                pilot, "#transfer_behav_checkbox"
            )  # and these on...
            await self.scroll_to_click_pause(
                pilot, "#transfer_funcimg_checkbox"
            )

            await self.run_transfer(pilot, upload_or_download)

            folders_used = test_utils.get_all_folders_used(value=False)
            folders_used.update({"behav": True, "funcimg": True})

            test_utils.check_working_top_level_folder_only_exists(
                top_level_folder,
                base_path_to_check / top_level_folder,
                [sub_to_transfer],
                [ses_to_transfer],
                folders_used,
            )

            await pilot.pause()

    async def switch_top_level_folder_select(
        self, pilot, id, top_level_folder
    ):

        if top_level_folder == "rawdata":
            assert pilot.app.screen.query_one(id).value == "rawdata"
        else:
            await self.move_select_to_position(pilot, id, position=5)
            assert pilot.app.screen.query_one(id).value == "derivatives"

    async def run_transfer(self, pilot, upload_or_download):
        """"""
        # Check assumed default is correct on the transfer switch
        assert pilot.app.screen.query_one("#transfer_switch").value is False

        if upload_or_download == "download":
            await self.scroll_to_click_pause(pilot, "#transfer_switch")

        await self.scroll_to_click_pause(pilot, "#transfer_transfer_button")
        await self.scroll_to_click_pause(pilot, "#confirm_ok_button")

    def setup_project_for_data_transfer(
        self,
        project,
        subs,
        sessions,
        top_level_folder_list,
        upload_or_download,
    ):
        """"""
        for top_level_folder in top_level_folder_list:
            test_utils.make_and_check_local_project_folders(
                project,
                top_level_folder,
                subs,
                sessions,
                "all",
            )
        (
            _,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        return base_path_to_check
