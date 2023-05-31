import pytest
import test_utils

from datashuttle.datashuttle import DataShuttle

TEST_PROJECT_NAME = "test_persistent_settings"


class TestPersistentSettings:
    @pytest.fixture(scope="function")
    def project(self, tmp_path):
        """
        Setup a project with default configs to use
        for testing.

        # Note this fixture is a duplicate of project()
        in test_filesystem_transfer.py fixture
        """

        setup_project, cwd = test_utils.setup_project_fixture(
            tmp_path, TEST_PROJECT_NAME
        )

        default_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=True
        )
        setup_project.make_config_file(**default_configs)

        yield setup_project
        test_utils.teardown_project(cwd, setup_project)

    # -------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------

    @pytest.mark.parametrize("unused_repeat", [1, 2])
    def test_persistent_settings(self, project, unused_repeat):
        """
        Test persistent settings functions by editing the
        persistent settings, checking they are changed and
        the program settings are changed accordingly.
        """
        settings = project._load_persistent_settings()

        assert len(settings) == 1
        assert settings["top_level_folder"] == "rawdata"

        # Update they persistent setting and check this is reflected
        # in a newly loading version of the settings
        project._update_persistent_setting("top_level_folder", "derivatives")

        settings_changed = project._load_persistent_settings()
        assert settings_changed["top_level_folder"] == "derivatives"

        # Re-load the project - this should now take top_level_folder
        # from the new persistent settings
        project_reload = DataShuttle(TEST_PROJECT_NAME)
        assert project_reload.cfg.top_level_folder_name == "derivatives"

        # Delete the persistent settings .yaml and check the next
        # time a project is loaded, it is initialized gracefully to the
        # default value.
        (
            project_reload._datashuttle_path / "persistent_settings.yaml"
        ).unlink()

        fresh_project = DataShuttle(TEST_PROJECT_NAME)

        assert fresh_project.cfg.top_level_folder_name == "rawdata"

    def test_set_top_level_folder_is_persistent(self, project):
        """
        Test that set_top_level_folder_name sets the top
        level folder name persistently across sessions.
        """
        assert project.cfg.top_level_folder_name == "rawdata"

        project.set_top_level_folder("derivatives")

        assert project.cfg.top_level_folder_name == "derivatives"

        project_reload = DataShuttle(TEST_PROJECT_NAME)

        assert project_reload.cfg.top_level_folder_name == "derivatives"

        stdout = test_utils.run_cli(
            " show-top-level-folder", TEST_PROJECT_NAME
        )

        assert "The working top level folder is: derivatives" in stdout[0]
