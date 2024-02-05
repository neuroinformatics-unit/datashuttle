import pytest

from datashuttle.tui.app import TuiApp
from datashuttle.tui.screens.new_project import NewProjectScreen

# pip install pytest-asyncio
# - anyio

# - pytest - asyncio
# - pytest - tornasync
# - pytest - trio
# - pytest - twisted


# https://stackoverflow.com/questions/55893235/pytest-skips-test-saying-asyncio-not-installed add to configs


# Select Existing Project

# Make New Project


# test mainmenu button
# test with ssh
# test without ssh
# test bad ssh
# test some configs errors
# class TestTUI:
class CallbackCompleted(BaseException):
    def __init__(self):
        pass


async def scroll_to_widget(pilot, widget):
    widget.scroll_visible(animate=False)
    await pilot.pause()


# TODO: need to add to
@pytest.mark.asyncio
async def test_make_new_project_local_filesystem_set_1(tmp_path, monkeypatch):

    project_name_test = "my-test-project"
    local_path_test = tmp_path / "local" / project_name_test
    connection_method_test = "local_filesystem"
    central_path_test = tmp_path / "central" / project_name_test

    local_path_test.mkdir(parents=True)
    central_path_test.mkdir(parents=True)
    overwrite_old_files_test = True

    def mocked_make_config_file(
        self,
        local_path,
        central_path,
        connection_method,
        central_host_id=None,
        central_host_username=None,
        overwrite_old_files=False,
        transfer_verbosity="v",
        show_transfer_progress=False,
    ):
        assert local_path == local_path_test
        assert central_path == central_path_test
        assert connection_method == connection_method_test
        assert overwrite_old_files == overwrite_old_files_test

        assert central_host_id is None
        assert central_host_username is None
        assert transfer_verbosity == "v"
        assert show_transfer_progress is False

    # Mock!
    app = TuiApp()
    async with app.run_test() as pilot:

        await pilot.click("#mainwindow_new_project_button")
        await pilot.pause()

        assert pilot.app.screen_stack[0].id == "_default"
        assert isinstance(pilot.app.screen_stack[1], NewProjectScreen)
        assert pilot.app.screen_stack[1].title == "Make New Project"

        configs_content = pilot.app.screen_stack[1].query_one(
            "#new_project_configs_content"
        )

        # Top Labels
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
            == "Set your configurations for a new project. For more details on each section,\nsee the Datashuttle documentation. Once configs are set, you will be able\nto use the 'Create' and 'Transfer' tabs."
        )

        # Project Name
        assert (
            configs_content.query_one("#configs_name_label").renderable._text[
                0
            ]
            == "Project Name"
        )
        assert configs_content.query_one("#configs_name_input").value == ""

        await pilot.click("#configs_name_input")
        await pilot.press(*project_name_test)
        assert (
            configs_content.query_one("#configs_name_input").value
            == project_name_test
        )

        # Local Path
        assert (
            configs_content.query_one(
                "#configs_local_path_label"
            ).renderable._text[0]
            == "Local Path"
        )

        await scroll_to_widget(
            pilot, configs_content.query_one("#configs_local_path_input")
        )
        await pilot.click("#configs_local_path_input")
        await pilot.press(*local_path_test.as_posix())
        assert (
            configs_content.query_one("#configs_local_path_input").value
            == local_path_test.as_posix()
        )

        # Connection Method
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

        # Central Path
        await scroll_to_widget(
            pilot, configs_content.query_one("#configs_central_path_input")
        )  # TODO: maybe own function across all tests
        await pilot.click("#configs_central_path_input")
        await pilot.press(*central_path_test.as_posix())
        assert (
            configs_content.query_one("#configs_central_path_input").value
            == central_path_test.as_posix()
        )

        # Transfer Options
        assert (
            configs_content.query_one(
                "#configs_transfer_options_container"
            ).border_title
            == "Transfer Options"
        )
        assert (
            configs_content.query_one(
                "#configs_overwrite_files_checkbox"
            ).value
            is False
        )

        await scroll_to_widget(
            pilot,
            configs_content.query_one("#configs_overwrite_files_checkbox"),
        )
        await pilot.click("#configs_overwrite_files_checkbox")

        assert (
            configs_content.query_one(
                "#configs_overwrite_files_checkbox"
            ).value
            is True
        )

        await scroll_to_widget(
            pilot, configs_content.query_one("#configs_save_configs_button")
        )

        monkeypatch.setattr(
            "datashuttle.datashuttle.DataShuttle.make_config_file",
            mocked_make_config_file,
        )

        await pilot.click("#configs_save_configs_button")
        await pilot.pause()  # avoid "Task was destroyed but it is pending!",  try in fixture
        assert (
            pilot.app.screen.query_one(
                "#messagebox_message_label"
            ).renderable._text[0]
            == "A DataShuttle project has now been created.\n\n Click 'OK' to proceed to the project page, where you will be able to create and transfer project folders."
        )

        await pilot.click("#messagebox_ok_button")
        await pilot.pause()
        assert (
            pilot.app.screen.query_one(
                "#messagebox_message_label"
            ).renderable._text[0]
            == "A DataShuttle project has now been created.\n\n Click 'OK' to proceed to the project page, where you will be able to create and transfer project folders."
        )

        await pilot.click("#messagebox_ok_button")
        await pilot.pause()
        breakpoint()

        # TODO: just test on actual datashuttle and configs, basically gonna make no difference!
        # also make sure all are checked.

        await pilot.pause()  # avoid "Task was destroyed but it is pending!",  try in fixture

        breakpoint()


# Settings

# Light / Dark mode
# DirectoryTree Setting
