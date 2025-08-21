import copy
from pathlib import Path
from time import monotonic

import pytest

from datashuttle.configs import load_configs
from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import (
    SelectDirectoryTreeScreen,
)

from .tui_configs_base import TuiConfigsBase


class TestTuiConfigs(TuiConfigsBase):
    # -------------------------------------------------------------------------
    # Test New Project Configs
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    @pytest.mark.parametrize("kwargs_set", [1, 2])
    async def test_make_new_project_configs(
        self,
        empty_project_paths,
        kwargs_set,
    ):
        """Check the ConfigsContent when making a new project. This contains
        many widgets shared with the ConfigsContent on the tab page, however
        also includes an additional information banner and input for the
        project name.

        Here check these widgets are display correctly, and fill them. Next
        check the config widgets are empty, then fill the widgets, save,
        and check the interface.project and saved configs match the new
        settings.
        """
        tmp_config_path, tmp_path, project_name = empty_project_paths.values()

        kwargs = {
            "local_path": (tmp_path / "local" / project_name).as_posix(),
            # not used in TUI, set to `make_config_file` defaults.
            "central_path": (tmp_path / "central" / project_name).as_posix(),
        }

        if kwargs_set == 1:
            kwargs.update(
                {
                    "connection_method": "local_filesystem",
                    "central_host_id": None,
                    "central_host_username": None,
                }
            )
        elif kwargs_set == 2:
            kwargs.update(
                {
                    "connection_method": "ssh",
                    "central_host_id": "@test.host.id",
                    "central_host_username": "test_username",
                }
            )

        Path(kwargs["local_path"]).parent.mkdir(parents=True)
        Path(kwargs["central_path"]).parent.mkdir(parents=True)

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.run_and_test_new_project_configs(
                pilot,
                project_name,
                tmp_config_path,
                connection_method_name="SSH" if kwargs_set == 2 else "",
                config_kwargs=kwargs,
            )

    # -------------------------------------------------------------------------
    # Test Existing Project Configs
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_config_on_project_manager_screen(
        self, setup_project_paths
    ):
        """Test the ConfigsContent on the project manager tab screen.
        The project is set up in the fixture, navigate to the project page.
        Check that the default configs are displayed. Change all the configs,
        save, and check these are updated on the config file and on the
        `project` stored in `interface`.

        Next, exit out of the project with the "Main Menu" button, go back
        into the project and check the new configs are displayed.
        """
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Navigate to the existing project and click onto the
            # configs tab.
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.switch_tab(pilot, "configs")

            configs_content = pilot.app.screen.query_one(
                "#tabscreen_configs_content"
            )

            # Now get the default datashuttle configs, and check they match
            # those displayed on the ConfigsContent.
            project_cfg = copy.deepcopy(pilot.app.screen.interface.project.cfg)
            load_configs.convert_str_and_pathlib_paths(
                project_cfg, "path_to_str"
            )

            await self.check_configs_widgets_match_configs(
                configs_content, project_cfg
            )

            # Now we make some new settings, and set the ConfigsContent.
            # Make sure they are all different to the existing configs,
            # then save and check the configs on the DataShuttle instance
            # and file are updated.

            new_kwargs = {
                "local_path": self.make_and_get_random_project_path(
                    tmp_path, project_name
                ),
                "central_path": self.make_and_get_random_project_path(
                    tmp_path, project_name
                ),
                "connection_method": "ssh",
                "central_host_id": "random_host",
                "central_host_username": "random_username",
            }
            await self.edit_configs_and_check_widgets(
                pilot, tmp_config_path, project_name, new_kwargs, project_cfg
            )

    # -------------------------------------------------------------------------
    # Test the config page widgets
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_configs_select_path(self, monkeypatch):
        """Test the 'Select' buttons / DirectoryTree on the ConfigsContent.
        These are used to select folders that are filled into the Input.
        Open the select dialog, select a folder, check the path is
        filled into the Input. There is one for both local
        and central path.

        When SSH is selected, the central path 'Select' should be disabled,
        as it only makes sense to choose this for local filesystem transfer.
        """
        self.monkeypatch_print(monkeypatch)

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Select the page and ConfigsContent for setting up new project
            await self.scroll_to_click_pause(
                pilot, "#mainwindow_new_project_button"
            )

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
                ["#configs_local_path_input", "#configs_central_path_input"],
            ):
                await self.scroll_to_click_pause(
                    pilot,
                    f"#{select_button.id}",
                )

                assert isinstance(pilot.app.screen, SelectDirectoryTreeScreen)

                tree = pilot.app.screen.query_one(
                    "#select_directory_tree_directory_tree"
                )
                root_path = tree.root.data.path

                pilot.app.screen.click_info.prev_click_widget_id = tree.id
                pilot.app.screen.click_info.prev_click_time = monotonic()

                pilot.app.screen.on_directory_tree_directory_selected(
                    tree.DirectorySelected(tree.root, root_path)
                )
                await pilot.pause()

                assert (
                    configs_content.query_one(path_input_id).value
                    == root_path.as_posix()
                )

                await pilot.pause()

            # Check the central path only is not displayed in SSH mode.
            assert local_path_button.display is True
            assert central_path_button.display is True

            await self.scroll_to_click_pause(pilot, "#configs_ssh_radiobutton")

            assert local_path_button.display is True
            assert central_path_button.display is False

            await pilot.pause()

    @pytest.mark.asyncio
    async def test_bad_configs_screen_input(self, empty_project_paths):
        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Select a new project, check NewProjectScreen is displayed correctly.
            await self.scroll_to_click_pause(
                pilot, "#mainwindow_new_project_button"
            )

            await self.fill_input(pilot, "#configs_name_input", "a@@")
            await self.fill_input(pilot, "#configs_local_path_input", "a")
            await self.fill_input(pilot, "#configs_central_path_input", "b")
            await self.scroll_to_click_pause(
                pilot, "#configs_save_configs_button"
            )

            assert (
                pilot.app.screen.query_one(
                    "#messagebox_message_label"
                ).renderable
                == "The project name must contain alphanumeric characters only."
            )
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_switch_connection_radiobuttons(self):
        """Test correct widgets being displayed for each connection method"""
        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Select the page and ConfigsContent for setting up new project
            await self.scroll_to_click_pause(
                pilot, "#mainwindow_new_project_button"
            )

            configs_content = pilot.app.screen.query_one(
                "#new_project_configs_content"
            )

            ssh_widgets = configs_content.config_ssh_widgets
            gdrive_widgets = configs_content.config_gdrive_widgets
            aws_widgets = configs_content.config_aws_widgets

            for connection_method in ["ssh", "gdrive", "aws"]:
                await self.switch_and_check_widgets_display(
                    pilot,
                    connection_method,
                    ssh_widgets,
                    gdrive_widgets,
                    aws_widgets,
                )

    # -------------------------------------------------------------------------
    # Test project name is number
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_project_name_is_number(self, empty_project_paths):
        """
        Make a project that has a number name, and check the project screen
        can be loaded.
        """
        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Set up a project with a numerical project name
            project_name = "123"

            await self.scroll_to_click_pause(
                pilot, "#mainwindow_new_project_button"
            )

            await self.fill_input(pilot, "#configs_name_input", project_name)
            await self.fill_input(pilot, "#configs_local_path_input", "a")
            await self.fill_input(pilot, "#configs_central_path_input", "b")
            await self.scroll_to_click_pause(
                pilot, "#configs_save_configs_button"
            )

            # Go back to main menu and load the project screen
            await self.close_messagebox(pilot)

            await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")

            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await pilot.pause()
