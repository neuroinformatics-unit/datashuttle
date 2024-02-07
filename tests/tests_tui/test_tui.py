from pathlib import Path

import pytest
import pytest_asyncio
import test_utils
from textual.widgets._tabbed_content import ContentTab

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.modal_dialogs import SelectDirectoryTreeScreen
from datashuttle.tui.screens.new_project import NewProjectScreen
from datashuttle.tui.screens.project_manager import ProjectManagerScreen
from datashuttle.tui.screens.project_selector import ProjectSelectorScreen

# TODO: carefully check configs tests after refactor!

# https://stackoverflow.com/questions/55893235/pytest-skips-test-saying-asyncio-not
# -installed add to configs

# need to allow name templates to be sub oR ses
# Select Existing Project

# Make New Project
# TODO: add green to light mode css

# TODO: could do CTRL+D to input to delete all content .

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
    # but don't do for any other tests because 1) command_line_interface issue
    # and 2) it is further away from real use case.

    @pytest_asyncio.fixture(scope="function")
    async def empty_project_paths(self, tmp_path_factory, monkeypatch):
        """ """
        tmp_path = tmp_path_factory.mktemp("test")
        tmp_config_path = tmp_path / "config"

        self.monkeypatch_get_datashuttle_path(tmp_config_path, monkeypatch)
        self.monkeypatch_print(monkeypatch)

        assert not any(tmp_config_path.glob("**"))

        yield [tmp_config_path, tmp_path]

    @pytest_asyncio.fixture(scope="function")
    async def setup_project_paths(self, tmp_path_factory, monkeypatch):
        """"""
        project_name = "my-test-project"  # TODO: global?
        tmp_path = tmp_path_factory.mktemp("test")
        tmp_config_path = tmp_path / "config"

        self.monkeypatch_get_datashuttle_path(tmp_config_path, monkeypatch)
        self.monkeypatch_print(monkeypatch)

        test_utils.setup_project_fixture(tmp_path, project_name)

        return [tmp_config_path, tmp_path, project_name]

    def monkeypatch_get_datashuttle_path(self, tmp_config_path, _monkeypatch):

        def mock_get_datashuttle_path():
            return tmp_config_path

        _monkeypatch.setattr(
            "datashuttle.configs.canonical_folders.get_datashuttle_path",
            mock_get_datashuttle_path,
        )

    def monkeypatch_print(self, _monkeypatch):

        def return_none(arg1, arg2=None):
            return

        _monkeypatch.setattr(
            "datashuttle.utils.utils.print_message_to_user", return_none
        )

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
        """ """
        tmp_config_path, tmp_path = empty_project_paths  # TODO: use dict

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

            await self.check_new_project_configs(
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

    async def check_and_click_onto_existing_project(self, pilot, project_name):
        """ """
        await pilot.click("#mainwindow_existing_project_button")

        assert isinstance(pilot.app.screen, ProjectSelectorScreen)
        assert len(pilot.app.screen.project_names) == 1
        assert project_name in pilot.app.screen.project_names

        await pilot.click(f"#{project_name}")

        assert isinstance(pilot.app.screen, ProjectManagerScreen)
        assert pilot.app.screen.title == f"Project: {project_name}"
        assert (
            pilot.app.screen.query_one("#tabscreen_tabbed_content").active
            == "tabscreen_create_tab"
        )

    @pytest.mark.asyncio
    async def test_update_config_on_project_manager_screen(
        self, setup_project_paths
    ):
        """"""
        tmp_config_path, tmp_path, project_name = setup_project_paths

        app = TuiApp()
        async with app.run_test() as pilot:
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await pilot.click(
                f"Tab#{ContentTab.add_prefix('tabscreen_configs_tab')}"
            )  # see  https://github.com/Textualize/textual/blob/main/tests/test_tabbed_content.py

            configs_content = pilot.app.screen.query_one(
                "#tabscreen_configs_content"
            )
            import copy

            project_cfg = copy.deepcopy(pilot.app.screen.interface.project.cfg)
            project_cfg.convert_str_and_pathlib_paths(
                project_cfg, "path_to_str"
            )  # this syntax is so weird.

            await self.check_configs_widgets_match_configs(
                pilot, configs_content, project_cfg
            )

            # TODO: rename
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
                pilot, configs_content, new_kwargs
            )

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one("#configs_save_configs_button"),
            )
            assert (
                pilot.app.screen.query_one(
                    "#messagebox_message_label"
                ).renderable._text[0]
                == "Configs saved."
            )

            pilot.app.screen.on_button_pressed()  # for some reason clicking does not work...
            await pilot.pause()

            test_utils.check_configs(
                pilot.app.screen.interface.project,
                new_kwargs,
                tmp_config_path / project_name / "config.yaml",
            )

            await self.scroll_to_click_pause(
                pilot, pilot.app.screen.query_one("#all_main_menu_buttons")
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
            )  # I guess this is necessary

            await self.check_configs_widgets_match_configs(
                pilot, configs_content, new_kwargs
            )
            await pilot.pause()

    # test all create files at once
    # test all keyboard shortcuts
    # test template validation settings etc.

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def scroll_to_and_pause(self, pilot, widget):
        widget.scroll_visible(animate=False)
        await pilot.pause()

    async def scroll_to_click_pause(self, pilot, widget):
        await self.scroll_to_and_pause(pilot, widget)
        await pilot.click(f"#{widget.id}")
        await pilot.pause()

    async def check_configs_widgets_match_configs(
        self, pilot, configs_content, kwargs
    ):

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
            assert configs_content.query_one(id).display is ssh_widgets_display

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

    async def check_new_project_configs(
        self, pilot, project_name, configs_content, kwargs
    ):

        # New Project Labels --------------------------------------------------

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

        # Project Name --------------------------------------------------------

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

        # Shared Config Widgets -----------------------------------------------

        default_kwargs = {
            "local_path": "",
            "central_path": "",
            "connection_method": "local_filesystem",
            "overwrite_old_files": False,
        }
        await self.check_configs_widgets_match_configs(
            pilot, configs_content, default_kwargs
        )
        await self.set_configs_content_widgets(pilot, configs_content, kwargs)
        await self.check_configs_widgets_match_configs(
            pilot, configs_content, kwargs
        )

    async def set_configs_content_widgets(
        self, pilot, configs_content, kwargs
    ):
        """ """

        # Local Path ----------------------------------------------------------

        assert (
            configs_content.query_one(
                "#configs_local_path_label"
            ).renderable._text[0]
            == "Local Path"
        )

        configs_content.query_one("#configs_local_path_input").value = ""
        await self.scroll_to_click_pause(
            pilot, configs_content.query_one("#configs_local_path_input")
        )
        await pilot.press(*kwargs["local_path"])

        # Connection Method ---------------------------------------------------

        if kwargs["connection_method"] == "ssh":

            await self.scroll_to_click_pause(
                pilot, configs_content.query_one("#configs_ssh_radiobutton")
            )

            # Central Host ID -------------------------------------------------

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one("#configs_central_host_id_input"),
            )
            await pilot.press(*kwargs["central_host_id"])

            # Central Host Username -------------------------------------------

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one(
                    "#configs_central_host_username_input"
                ),
            )
            await pilot.press(*kwargs["central_host_username"])

        # Central Path --------------------------------------------------------

        configs_content.query_one("#configs_central_path_input").value = ""
        await self.scroll_to_click_pause(
            pilot, configs_content.query_one("#configs_central_path_input")
        )
        await pilot.press(*kwargs["central_path"])

        # Overwrite Files -----------------------------------------------------

        if kwargs["overwrite_old_files"]:

            await self.scroll_to_click_pause(
                pilot,
                configs_content.query_one("#configs_overwrite_files_checkbox"),
            )


# Settings

# Light / Dark mode
# DirectoryTree Setting
