import pytest
import test_utils
from base import BaseTest

from datashuttle import DataShuttle


class TestPersistentSettings(BaseTest):
    @pytest.mark.parametrize("unused_repeat", [1, 2])
    def test_persistent_settings(self, project, unused_repeat):
        """
        Test persistent settings functions by editing the
        persistent settings, checking they are changed and
        the program settings are changed accordingly.
        """
        settings = project._load_persistent_settings()

        assert len(settings) == 2
        assert settings["top_level_folder"] == "rawdata"

        # Update they persistent setting and check this is reflected
        # in a newly loading version of the settings
        project._update_persistent_setting("top_level_folder", "derivatives")

        settings_changed = project._load_persistent_settings()
        assert settings_changed["top_level_folder"] == "derivatives"

        # Re-load the project - this should now take top_level_folder
        # from the new persistent settings
        project_reload = DataShuttle(project.project_name)
        assert project_reload.cfg.top_level_folder == "derivatives"

        # Delete the persistent settings .yaml and check the next
        # time a project is loaded, it is initialized gracefully to the
        # default value.
        (
            project_reload._datashuttle_path / "persistent_settings.yaml"
        ).unlink()

        fresh_project = DataShuttle(project.project_name)

        assert fresh_project.cfg.top_level_folder == "rawdata"

    def test_set_top_level_folder_is_persistent(self, project):
        """
        Test that set_top_level_folder sets the top
        level folder name persistently across sessions.
        """
        assert project.cfg.top_level_folder == "rawdata"

        project.set_top_level_folder("derivatives")

        assert project.cfg.top_level_folder == "derivatives"

        project_reload = DataShuttle(project.project_name)

        assert project_reload.cfg.top_level_folder == "derivatives"

        stdout = test_utils.run_cli(
            " get-top-level-folder", project.project_name
        )

        assert "derivatives" in stdout[0]
