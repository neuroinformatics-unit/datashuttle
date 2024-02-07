from pathlib import Path

import pytest
import test_utils

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import SelectDirectoryTreeScreen
from datashuttle.tui.screens.new_project import NewProjectScreen
from datashuttle.tui.screens.project_manager import ProjectManagerScreen

# pip install pytest-asyncio
# - anyio

# - pytest - asyncio
# - pytest - tornasync
# - pytest - trio
# - pytest - twisted


# https://stackoverflow.com/questions/55893235/pytest-skips-test-saying-asyncio-not
# -installed add to configs


# Select Existing Project

# Make New Project


# test mainmenu button
# test with ssh
# test without ssh
# test bad ssh
# test some configs errors

# TODO: need to check Selects + whether they are disabled.
# Test everything mocl
# Sanity check just check it actually works
# TODO: ssh setup not tested, need images!


class TestTUI:
    # Just make a break here, and set configs also in the tmp_config
    # but dont do for any other tests because 1) command_line_interface issue
    # and 2) it is further away from real use case.
    async def scroll_to_and_pause(self, pilot, widget):
        widget.scroll_visible(animate=False)
        await pilot.pause()

    async def scroll_to_click_pause(self, pilot, widget):
        await self.scroll_to_and_pause(pilot, widget)
        await pilot.click(f"#{widget.id}")
        await pilot.pause()

    def setup_project(self, _tmp_path, _monkeypatch):
        """ """
        tmp_config_path = _tmp_path / "config"

        def mock_get_datashuttle_path():
            return tmp_config_path

        _monkeypatch.setattr(
            "datashuttle.configs.canonical_folders.get_datashuttle_path",
            mock_get_datashuttle_path,
        )

        self.monkeypatch_print(_monkeypatch)

        assert not any(tmp_config_path.glob("**"))

        return tmp_config_path

    def monkeypatch_print(self, _monkeypatch):

        def return_none(arg1, arg2=None):
            return

        _monkeypatch.setattr(
            "datashuttle.utils.utils.print_message_to_user", return_none
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("kwargs_set", [1, 2])
    async def test_make_new_project_local_filesystem_set_1(
        self, kwargs_set, tmp_path, monkeypatch
    ):
        """ """
        tmp_config_path = self.setup_project(tmp_path, monkeypatch)

        project_name = "my-test-project"

        kwargs = {
            "local_path": (tmp_path / "local" / project_name).as_posix(),
            # not used in TUI, set to `make_config_file` defaults.
            "central_path": (tmp_path / "central" / project_name).as_posix(),
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
            await pilot.click("#mainwindow_new_project_button")
            await pilot.pause()

            assert pilot.app.screen_stack[0].id == "_default"
            assert isinstance(pilot.app.screen_stack[1], NewProjectScreen)
            assert pilot.app.screen_stack[1].title == "Make New Project"

            configs_content = pilot.app.screen.query_one(
                "#new_project_configs_content"
            )

            await self.check_and_set_configs_content_widgets(
                pilot, project_name, configs_content, kwargs
            )

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one("#configs_save_configs_button"),
            )

            assert (
                pilot.app.screen.query_one(
                    "#messagebox_message_label"
                ).renderable._text[0]
                == "A DataShuttle project has now been created.\n\n Click 'OK' to "
                "proceed to the project page, where you will be able to create and "
                "transfer project folders."
            )

            pilot.app.screen.on_button_pressed()  # for some reason clicking does not work...
            await pilot.pause()

            assert isinstance(pilot.app.screen, ProjectManagerScreen)

            test_utils.check_configs(
                pilot.app.screen.interface.project,
                kwargs,
                tmp_config_path / project_name / "config.yaml",
            )

    @pytest.mark.asyncio
    async def test_configs_select_path(self, monkeypatch):

        self.monkeypatch_print(monkeypatch)

        app = TuiApp()
        async with app.run_test() as pilot:
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

            for select_button, path_input_id in zip(
                [local_path_button, central_path_button],
                ["#configs_local_path_input", "#configs_central_path_input"],
            ):
                await self.scroll_to_click_pause(
                    pilot,
                    select_button,
                )

                assert isinstance(pilot.app.screen, SelectDirectoryTreeScreen)

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

            # Now check displayed!
            assert local_path_button.disabled is False
            assert central_path_button.disabled is False

            await self.scroll_to_click_pause(
                pilot, configs_content.query_one("#configs_ssh_radiobutton")
            )

            assert local_path_button.disabled is False
            assert central_path_button.disabled is True

    #    async def

    async def check_and_set_configs_content_widgets(
        self, pilot, project_name, configs_content, kwargs
    ):
        """ """

        # Top Labels -------------------------------------------------------------------

        assert (
            configs_content.query_one(
                "#configs_banner_label"
            ).renderable._text[0]
            == "Configure A New Project"
        )
        assert (
            configs_content.query_one("#configs_info_label").renderable._text[
                0
            ]
            == "Set your configurations for a new project. For more details on "
            "each section,\nsee the Datashuttle documentation. Once configs "
            "are set, you will be able\nto use the 'Create' and 'Transfer' tabs."
        )

        # Project Name -----------------------------------------------------------------

        assert (
            configs_content.query_one("#configs_name_label").renderable._text[
                0
            ]
            == "Project Name"
        )
        assert configs_content.query_one("#configs_name_input").value == ""

        await pilot.click("#configs_name_input")
        await pilot.press(*project_name)
        assert (
            configs_content.query_one("#configs_name_input").value
            == project_name
        )

        # Local Path -------------------------------------------------------------------

        assert (
            configs_content.query_one(
                "#configs_local_path_label"
            ).renderable._text[0]
            == "Local Path"
        )
        assert (
            configs_content.query_one("#configs_local_path_input").value == ""
        )  # TODO: these input checks are extremely formulaeic

        await self.scroll_to_click_pause(
            pilot, configs_content.query_one("#configs_local_path_input")
        )
        await pilot.press(*kwargs["local_path"])
        assert (
            configs_content.query_one("#configs_local_path_input").value
            == kwargs["local_path"]
        )

        # Connection Method ------------------------------------------------------------

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

        if kwargs["connection_method"] == "ssh":

            await self.scroll_to_click_pause(
                pilot, configs_content.query_one("#configs_ssh_radiobutton")
            )

            # Central Host ID ----------------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_central_host_id_label"
                ).renderable._text[0]
                == "Central Host ID"
            )

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one("#configs_central_host_id_input"),
            )
            await pilot.press(*kwargs["central_host_id"])
            assert (
                configs_content.query_one(
                    "#configs_central_host_id_input"
                ).value
                == kwargs["central_host_id"]
            )

            # Central Host Username ----------------------------------------------------

            assert (
                configs_content.query_one(
                    "#configs_central_host_username_label"
                ).renderable._text[0]
                == "Central Host Username"
            )

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one(
                    "#configs_central_host_username_input"
                ),
            )
            await pilot.press(*kwargs["central_host_username"])
            assert (
                configs_content.query_one(
                    "#configs_central_host_username_input"
                ).value
                == kwargs["central_host_username"]
            )

            ssh_widgets_display = True
        else:
            ssh_widgets_display = False

        # SSH widget display -----------------------------------------------------------

        for id in [
            "#configs_central_host_id_label",
            "#configs_central_host_id_input",
            "#configs_central_host_username_label",
            "#configs_central_host_username_input",
        ]:
            assert configs_content.query_one(id).display is ssh_widgets_display

        # Central Path -----------------------------------------------------------------

        await self.scroll_to_click_pause(
            pilot, configs_content.query_one("#configs_central_path_input")
        )
        await pilot.press(*kwargs["central_path"])
        assert (
            configs_content.query_one("#configs_central_path_input").value
            == kwargs["central_path"]
        )

        # Transfer Options -------------------------------------------------------------

        assert (
            configs_content.query_one(
                "#configs_transfer_options_container"
            ).border_title
            == "Transfer Options"
        )

        # Overwrite Files --------------------------------------------------------------

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

        if kwargs["overwrite_old_files"]:

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one("#configs_overwrite_files_checkbox"),
            )
            assert (
                configs_content.query_one(
                    "#configs_overwrite_files_checkbox"
                ).value
                is True
            )


# Settings

# Light / Dark mode
# DirectoryTree Setting
