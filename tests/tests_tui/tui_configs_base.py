from pathlib import Path
from typing import List
from uuid import uuid4

from textual.widget import Widget

from datashuttle.configs.canonical_configs import get_connection_methods_list
from datashuttle.tui.screens.project_manager import ProjectManagerScreen
from datashuttle.tui.utils import tui_utils

from .. import test_utils
from .tui_base import TuiBase


class TuiConfigsBase(TuiBase):
    """Contains helper functions for TUI tests of the configs tab."""

    async def run_and_test_new_project_configs(
        self,
        pilot,
        project_name,
        tmp_config_path,
        connection_method_name,
        config_kwargs,
    ):
        """Check the ConfigsContent widgets are displayed correctly are displayed
        correctly when making a new project. Fill these widgets with `config_kwargs`,
        save them, and check the interface.project and saved configs match the new
        settings.
        """
        assert pilot.app.screen.id == "_default"

        # Select a new project, check NewProjectScreen is
        # displayed correctly.
        await self.scroll_to_click_pause(
            pilot, "#mainwindow_new_project_button"
        )

        # Get the ConfigsContent and check all configs are displayed
        # correctly. `check_new_project_configs` checks empty defaults
        # are displayed, then updates with the kwargs and checks.
        configs_content = pilot.app.screen.query_one(
            "#new_project_configs_content"
        )

        await self.check_new_project_configs(
            pilot, project_name, configs_content, config_kwargs
        )

        # Save the configs and check the correct messages are shown.
        await self.scroll_to_click_pause(
            pilot,
            "#configs_save_configs_button",
        )

        if config_kwargs["connection_method"] == "local_filesystem":
            assert (
                pilot.app.screen.query_one("#messagebox_message_label")
                .render()
                .plain
                == "A datashuttle project has now been created.\n\n "
                "Next proceed to the project page, where you will "
                "be able to create and transfer project folders."
            )
            await self.close_messagebox(pilot)
        else:
            assert (
                pilot.app.screen.query_one("#messagebox_message_label")
                .render()
                .plain
                == tui_utils.get_project_created_message_template().format(
                    method_name=connection_method_name
                )
            )

            await self.close_messagebox(pilot)
            assert (
                pilot.app.screen.query_one(
                    "#configs_setup_connection_button"
                ).label
                == f"Setup {connection_method_name} Connection"
            )

        if connection_method_name == "Local Filesystem":
            # This is only shown after connection set up for ssh.
            assert (
                pilot.app.screen.query_one(
                    "#configs_go_to_project_screen_button"
                ).visible
                is True
            )

            await self.scroll_to_click_pause(
                pilot, "#configs_go_to_project_screen_button"
            )
            assert isinstance(pilot.app.screen, ProjectManagerScreen)

            project = pilot.app.screen.interface.project

            assert (
                pilot.app.screen.interface.project.project_name == project_name
            )

        # After saving, check all configs are correct on the DataShuttle
        # instance as well as the stored configs.
        test_utils.check_configs(
            project,
            config_kwargs,
            tmp_config_path / project_name / "config.yaml",
        )

        await pilot.pause()

    async def check_new_project_configs(
        self, pilot, project_name, configs_content, kwargs
    ):
        """Check the configs displayed on the TUI match those found in `kwargs`.
        Also, check the widgets unique to ConfigsContent on the
        configs selection for a new project.
        """
        # Project Name --------------------------------------------------------

        await self.fill_input(pilot, "#configs_name_input", project_name)
        assert (
            configs_content.query_one("#configs_name_input").value
            == project_name
        )

        # Shared Config Widgets -----------------------------------------------

        default_kwargs = {
            "local_path": "",
            "central_path": "",
            "connection_method": "local_only",
        }
        await self.check_configs_widgets_match_configs(
            configs_content, default_kwargs
        )
        await self.set_configs_content_widgets(pilot, kwargs)
        await self.check_configs_widgets_match_configs(configs_content, kwargs)

        await pilot.pause()

    async def edit_configs_and_check_widgets(
        self,
        pilot,
        tmp_config_path,
        project_name,
        new_kwargs,
        prev_project_cfg,
    ):
        """Set configs in the ConfigsContent tab to match `new_kwargs` and save them."""
        for key in new_kwargs:
            # The purpose is to update to completely new configs
            assert new_kwargs[key] != prev_project_cfg[key]

        configs_content = pilot.app.screen.query_one(
            "#tabscreen_configs_content"
        )

        await self.set_configs_content_widgets(pilot, new_kwargs)

        await self.check_configs_widgets_match_configs(
            configs_content, new_kwargs
        )

        await self.scroll_to_click_pause(
            pilot,
            "#configs_save_configs_button",
        )
        assert (
            pilot.app.screen.query_one("#messagebox_message_label")
            .render()
            .plain
            == "Configs saved."
        )
        await self.close_messagebox(pilot)

        test_utils.check_configs(
            pilot.app.screen.interface.project,
            new_kwargs,
            tmp_config_path / project_name / "config.yaml",
        )

        # Finally, use "Main Menu" button to go back to the home screen,
        # navigate back to the project and check the new configs are now
        # displayed.
        await self.scroll_to_click_pause(pilot, "#all_main_menu_buttons")
        assert pilot.app.screen.id == "_default"

        await self.check_and_click_onto_existing_project(pilot, project_name)
        await self.switch_tab(pilot, "configs")
        configs_content = pilot.app.screen.query_one(
            "#tabscreen_configs_content"
        )
        await self.check_configs_widgets_match_configs(
            configs_content, new_kwargs
        )

        await pilot.pause()

    async def check_configs_widgets_match_configs(
        self, configs_content, kwargs
    ):
        """Check that the widgets of the TUI configs match those found
        in `kwargs`.
        """
        # Local Path ----------------------------------------------------------

        assert (
            configs_content.query_one("#configs_local_path_input").value
            == kwargs["local_path"]
        )

        # Connection Method ---------------------------------------------------

        connection_method_to_label = {
            "local_filesystem": "Local Filesystem",
            "ssh": "SSH",
            "gdrive": "Google Drive",
            "aws": "AWS S3 Bucket",
            "local_only": "No connection (local only)",
        }
        label = connection_method_to_label[kwargs["connection_method"]]

        assert (
            configs_content.query_one(
                "#configs_connect_method_radioset"
            ).pressed_button.label._text
            == label
        )

        if kwargs["connection_method"] == "ssh":
            # Central Host ID -------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_central_host_id_input"
                ).value
                == kwargs["central_host_id"]
            )

            # Central Host Username -------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_central_host_username_input"
                ).value
                == kwargs["central_host_username"]
            )

        elif kwargs["connection_method"] == "gdrive":
            # Root Folder ID -------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_gdrive_root_folder_id_input",
                ).value
                == kwargs["gdrive_root_folder_id"]
            )

            # Gdrive Client ID -------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_gdrive_client_id_input",
                ).value
                == kwargs["gdrive_client_id"]
            )

        elif kwargs["connection_method"] == "aws":
            # AWS Access Key ID -------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_aws_access_key_id_input",
                ).value
                == kwargs["aws_access_key_id"]
            )

            # AWS Region -------------------------------------------

            select = configs_content.query_one("#configs_aws_region_select")
            assert select.value == kwargs["aws_region"]

        # Central Path --------------------------------------------------------

        assert (
            configs_content.query_one("#configs_central_path_input").value
            == kwargs["central_path"]
        )

    async def set_configs_content_widgets(self, pilot, kwargs):
        """Given a dict of options that can be set on the configs TUI
        in kwargs, set all configs widgets according to kwargs.
        """
        # Local Path ----------------------------------------------------------

        await self.fill_input(
            pilot, "#configs_local_path_input", kwargs["local_path"]
        )

        # Connection Method ---------------------------------------------------

        if kwargs["connection_method"] == "ssh":
            await self.scroll_to_click_pause(pilot, "#configs_ssh_radiobutton")

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

        elif kwargs["connection_method"] == "gdrive":
            await self.scroll_to_click_pause(
                pilot, "#configs_gdrive_radiobutton"
            )

            # Root Folder ID -------------------------------------------------

            await self.fill_input(
                pilot,
                "#configs_gdrive_root_folder_id_input",
                kwargs["gdrive_root_folder_id"],
            )

            # Gdrive Client ID -------------------------------------------

            await self.fill_input(
                pilot,
                "#configs_gdrive_client_id_input",
                kwargs["gdrive_client_id"],
            )

        elif kwargs["connection_method"] == "aws":
            await self.scroll_to_click_pause(pilot, "#configs_aws_radiobutton")

            # AWS Access Key ID -------------------------------------------------

            await self.fill_input(
                pilot,
                "#configs_aws_access_key_id_input",
                kwargs["aws_access_key_id"],
            )

            # AWS Region -------------------------------------------

            select = pilot.app.screen.query_one("#configs_aws_region_select")
            select.value = kwargs["aws_region"]
            await pilot.pause()

        elif kwargs["connection_method"] == "local_filesystem":
            await self.scroll_to_click_pause(
                pilot, "#configs_local_filesystem_radiobutton"
            )

        # Central Path --------------------------------------------------------

        await self.fill_input(
            pilot, "#configs_central_path_input", kwargs["central_path"]
        )

    async def switch_and_check_widgets_display(
        self,
        pilot,
        connection_method: str,
        ssh_widgets: List[Widget],
        gdrive_widgets: List[Widget],
        aws_widgets: List[Widget],
    ):
        """Switch radiobutton to a given `connection_method` and assert the presence of its widgets."""
        assert connection_method in get_connection_methods_list()
        await self.scroll_to_click_pause(
            pilot, f"#configs_{connection_method}_radiobutton"
        )

        widget_map = {
            "ssh": ssh_widgets,
            "gdrive": gdrive_widgets,
            "aws": aws_widgets,
        }

        for method, widgets in widget_map.items():
            for widget in widgets:
                assert widget.display == bool(method == connection_method)

    def make_and_get_random_project_path(
        self, tmp_path: Path, project_name: str
    ):
        random_path = tmp_path / f"{uuid4()}/{project_name}"
        random_path.mkdir(parents=True)
        return random_path.as_posix()
