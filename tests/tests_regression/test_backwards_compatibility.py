import shutil
from pathlib import Path

from datashuttle import DataShuttle


class TestBackwardsCompatibility:

    def test_v0_6_0(self):
        """
        v0.6.0 is the first version with narrow datatypes, and the checkboxes was refactored to
        be a {"on": bool, "displayed": bool} dict rather than a bool indicating whether the checkbox is on.
        However, this version is missing narrow datatypes added later (e.g. "motion").
        In the test file, all 'displayed' are turned off except f2pe.
        """
        reloaded_ver_configs, reloaded_ver_persistent_settings = (
            self.load_and_check_old_version_yamls("v0.6.0")
        )

        assert reloaded_ver_configs["local_path"] == Path("old_ver")

        reloaded_create_checkboxes = reloaded_ver_persistent_settings["tui"][
            "create_checkboxes_on"
        ]
        transfer_checkboxes = reloaded_ver_persistent_settings["tui"][
            "transfer_checkboxes_on"
        ]

        for key in reloaded_create_checkboxes.keys():
            assert reloaded_create_checkboxes[key]["displayed"] is (
                key == "f2pe"
            )

        for key in transfer_checkboxes.keys():
            assert transfer_checkboxes[key]["displayed"] is (key == "f2pe")

    def test_v0_5_3(self):
        """
        This version did not have narrow datatypes, and the persistent checkbox setting was only a
        bool. Therefore, the "displayed" uses the canonical defaults (because they don't exist in the file yet).
        """
        reloaded_ver_configs, reloaded_ver_persistent_settings = (
            self.load_and_check_old_version_yamls("v0.5.3")
        )

        assert reloaded_ver_configs["local_path"] == Path("old_ver")

        reloaded_create_checkboxes = reloaded_ver_persistent_settings["tui"][
            "create_checkboxes_on"
        ]
        transfer_checkboxes = reloaded_ver_persistent_settings["tui"][
            "transfer_checkboxes_on"
        ]

        assert reloaded_create_checkboxes["ephys"]["displayed"] is True
        assert reloaded_create_checkboxes["motion"]["displayed"] is False
        assert reloaded_create_checkboxes["f2pe"]["displayed"] is False

        assert transfer_checkboxes["ephys"]["displayed"] is True
        assert transfer_checkboxes["all"]["displayed"] is True
        assert transfer_checkboxes["motion"]["displayed"] is False
        assert transfer_checkboxes["f2pe"]["displayed"] is False

    def load_and_check_old_version_yamls(self, datashuttle_version):
        """
        Load an old config file in the current datashuttle version,
        and check that the new-version ('canonical') configs
        and persistent settings match the structure of the
        files loaded from the old datashuttle version.
        """
        project = DataShuttle("test_project")

        # Set up paths and clear any existing config files for this project
        old_version_path = (
            Path(__file__).parent / "old_version_configs" / datashuttle_version
        )

        config_file_path = project._config_path
        config_path = config_file_path.parent

        (config_file_path).unlink(missing_ok=True)
        (config_path / "persistent_settings.yaml").unlink(missing_ok=True)

        # In the current version of datashuttle, get the settings. These are
        # thus correct for the most recent datashuttle version.
        project = DataShuttle("test_project")
        project.make_config_file("cur_ver", "cur_ver", "local_filesystem")

        current_ver_configs = project.get_configs()
        current_ver_persistent_settings = project._load_persistent_settings()

        # Copy from the test paths the old version settings to the
        # project folder. Now when datashuttle loads, it will load from
        # these old version files. Check that these match the current version
        # files in structure.
        shutil.copy(old_version_path / "config.yaml", config_path)
        shutil.copy(old_version_path / "persistent_settings.yaml", config_path)

        project = DataShuttle("test_project")

        reloaded_ver_configs = project.get_configs()
        reloaded_ver_persistent_settings = project._load_persistent_settings()

        self.recursive_test_dictionary(
            current_ver_configs, reloaded_ver_configs
        )
        self.recursive_test_dictionary(
            current_ver_persistent_settings, reloaded_ver_persistent_settings
        )

        return reloaded_ver_configs, reloaded_ver_persistent_settings

    def recursive_test_dictionary(self, dict_canonical, dict_to_test):
        """
        A dictionary to check all keys in a nested dictionary
        match and all value types are the same.
        """
        keys_canonical = list(dict_canonical.keys())
        keys_to_test = list(dict_to_test.keys())

        assert keys_canonical == keys_to_test, (
            f"Keys are either missing or in the incorrect order:"
            f"\nkeys_canonical:\n {keys_canonical}"
            f"\nkeys_to_test:\n {keys_to_test}"
        )

        for key in dict_canonical.keys():

            if isinstance(dict_canonical[key], dict):
                self.recursive_test_dictionary(
                    dict_canonical[key], dict_to_test[key]
                )
            else:
                assert isinstance(
                    dict_to_test[key], type(dict_canonical[key])
                ), f"key: {key} is not the correct type"
