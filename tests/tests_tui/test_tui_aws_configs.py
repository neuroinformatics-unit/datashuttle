import copy

import pytest

from datashuttle.tui.app import TuiApp

from .tui_configs_base import TuiConfigsBase


class TestTuiAwsConfigs(TuiConfigsBase):
    # -------------------------------------------------------------------------
    # Test New Project Configs
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_make_new_project_configs(self, empty_project_paths):
        tmp_config_path, tmp_path, project_name = empty_project_paths.values()

        kwargs = {
            "local_path": (tmp_path / "local" / project_name).as_posix(),
            "central_path": (tmp_path / "central" / project_name).as_posix(),
            "connection_method": "aws",
            "aws_region": "us-east-1",
            "aws_access_key_id": "some-random-access-key-id",
        }

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            await self.run_and_test_new_project_configs(
                pilot,
                project_name,
                tmp_config_path,
                connection_method_name="AWS",
                config_kwargs=kwargs,
            )

    # -------------------------------------------------------------------------
    # Test Existing Project Configs
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_config_on_project_manager_screen(
        self, setup_project_paths
    ):
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test(size=self.tui_size()) as pilot:
            # Navigate to the existing project and click onto the
            # configs tab.
            await self.check_and_click_onto_existing_project(
                pilot, project_name
            )

            await self.switch_tab(pilot, "configs")

            project_cfg = copy.deepcopy(pilot.app.screen.interface.project.cfg)
            new_kwargs = {
                "local_path": self.make_and_get_random_project_path(
                    tmp_path, project_name
                ),
                "central_path": self.make_and_get_random_project_path(
                    tmp_path, project_name
                ),
                "connection_method": "aws",
                "aws_access_key_id": "random-access-key-id",
                "aws_region": "us-east-1",
            }

            await self.edit_configs_and_check_widgets(
                pilot, tmp_config_path, project_name, new_kwargs, project_cfg
            )
