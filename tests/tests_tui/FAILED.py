import pytest
from tui_base import TuiBase

from datashuttle.tui.app import TuiApp


class TuiFAILED(TuiBase):

    # FAILED TO IMPLEMENT
    @pytest.mark.asyncio
    async def __test_create_folders_directorytree_reload(
        self, setup_project_paths
    ):
        # TODO: this is not possible to implement because in test environment
        # we need fully refresh the tree just to be able to access it, not sure
        # this this this.
        pass
        tmp_config_path, tmp_path, project_name = setup_project_paths.values()

        app = TuiApp()
        async with app.run_test() as pilot:
            await self.setup_existing_project_create_tab_filled_sub_and_ses(
                pilot, project_name, create_folders=True
            )

            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 4
            )

            (
                pilot.app.screen.interface.project.cfg["local_path"]
                / "rawdata"
                / "sub-002"
            ).mkdir()

            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 4
            )

            assert (
                pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(2)
                .label._text[0]
                == "sub-001"
            )
            assert (
                pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(8)
                .label._text[0]
                is None
            )
            breakpoint()

            await self.press_tree(
                pilot,
                "#create_folders_directorytree",
                press_string="ctrl+r",
            )
            await self.reload_tree_nodes(
                pilot, "#create_folders_directorytree", 10
            )

            breakpoint()  # TODO: try and remove the above
            assert (
                pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(2)
                .label._text[0]
                == "sub-001"
            )
            assert (
                pilot.app.screen.query_one("#create_folders_directorytree")
                .get_node_at_line(8)
                .label._text[0]
                == "sub-002"
            )
